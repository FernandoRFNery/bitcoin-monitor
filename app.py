# First install required modules using:
# pip install requests flask

import requests
import time
from datetime import datetime
from flask import Flask, render_template_string, jsonify
from threading import Thread

app = Flask(__name__)

# Global variables for monitoring and price tracking
monitoring = False
monitor_thread = None
current_btc_price = 0
previous_btc_price = 0

def get_bitcoin_price():
    """Get current Bitcoin price from CoinGecko API"""
    try:
        response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd')
        return response.json()['bitcoin']['usd']
    except Exception as e:
        print(f"Error fetching Bitcoin price: {e}")
        return None

def send_whatsapp_alert(message):
    """Send WhatsApp message using CallMeBot"""
    try:
        # Send to first number
        url1 = f'https://api.callmebot.com/whatsapp.php?phone=555191961507&text={message}&apikey=1690058'
        response1 = requests.get(url1)
        if response1.status_code == 200:
            print(f"Alert sent successfully to first number")
        else:
            print(f"Error sending alert to first number: {response1.status_code}")

        # Send to second number
        url2 = f'https://api.callmebot.com/whatsapp.php?phone=555193752182&text={message}&apikey=1823567'
        response2 = requests.get(url2)
        if response2.status_code == 200:
            print(f"Alert sent successfully to second number")
        else:
            print(f"Error sending alert to second number: {response2.status_code}")
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")

def monitor_bitcoin():
    global monitoring, current_btc_price, previous_btc_price
    print("Bitcoin price monitoring started...")
    
    while monitoring:
        try:
            new_price = get_bitcoin_price()
            if new_price is not None:  # Only update if we got a valid price
                previous_btc_price = current_btc_price
                current_btc_price = new_price
                print(f"Price updated: ${current_btc_price:,.2f}")  # Debug print
                
                # Check for price drop and send alert
                if previous_btc_price > 0 and current_btc_price < previous_btc_price:
                    price_drop = ((previous_btc_price - current_btc_price) / previous_btc_price) * 100
                    message = (
                        f"⚠️ Bitcoin Alert!\n"
                        f"Price dropped by {price_drop:.2f}%\n"
                        f"Previous: ${previous_btc_price:,.2f}\n"
                        f"Current: ${current_btc_price:,.2f}\n"
                        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    send_whatsapp_alert(message)
                    
            time.sleep(20)  # Update every 20 seconds (3 times per minute)
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            time.sleep(60)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Bitcoin Price Monitor</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            text-align: center;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #ffffff;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            padding: 2rem;
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            border: 1px solid rgba(255, 255, 255, 0.18);
            margin: 20px;
            width: 80%;
            max-width: 600px;
        }
        h1 {
            color: #ffd700;
            font-size: 2.5em;
            margin-bottom: 30px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        .price { 
            font-size: 3.5em;
            margin: 30px;
            font-weight: bold;
            text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
            transition: color 0.3s ease;
        }
        .price.up {
            color: #00ff88;
        }
        .price.down {
            color: #ff4b2b;
        }
        .previous-price {
            font-size: 1.5em;
            color: #888;
            margin-top: -20px;
            margin-bottom: 20px;
        }
        .button { 
            padding: 15px 40px;
            font-size: 1.2em;
            cursor: pointer;
            background: linear-gradient(45deg, #00b4db, #0083b0);
            color: white;
            border: none;
            border-radius: 50px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 180, 219, 0.2);
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 180, 219, 0.4);
        }
        .button.stop { 
            background: linear-gradient(45deg, #ff416c, #ff4b2b);
            box-shadow: 0 4px 15px rgba(255, 65, 108, 0.2);
        }
        .button.stop:hover {
            box-shadow: 0 6px 20px rgba(255, 65, 108, 0.4);
        }
        .arrow {
            display: inline-block;
            margin-right: 10px;
        }
        .arrow.up {
            color: #00ff88;
        }
        .arrow.down {
            color: #ff4b2b;
        }
        .price-change {
            font-size: 0.4em;
            margin-right: 10px;
        }
        .price-change.up {
            color: #00ff88;
        }
        .price-change.down {
            color: #ff4b2b;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Bitcoin Price Monitor</h1>
        <div class="price">
            <span id="priceChange" class="price-change"></span>
            <span id="arrow" class="arrow"></span>$<span id="price">0.00</span>
        </div>
        <div class="previous-price">Previous: $<span id="previousPrice">0.00</span></div>
        <button onclick="toggleMonitoring()" id="monitorButton" class="button">Start Monitoring</button>
    </div>

    <script>
        let lastPrice = 0;
        
        function updatePrice() {
            fetch('/get_price')
                .then(response => response.json())
                .then(data => {
                    console.log("Received price data:", data); // Debug log
                    const priceElement = document.querySelector('.price');
                    const priceSpan = document.getElementById('price');
                    const previousPriceSpan = document.getElementById('previousPrice');
                    const arrowSpan = document.getElementById('arrow');
                    const priceChangeSpan = document.getElementById('priceChange');
                    const currentPrice = parseFloat(data.price);
                    
                    if (currentPrice > 0) {  // Only update if we have a valid price
                        priceSpan.textContent = currentPrice.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                        
                        if (lastPrice > 0 && currentPrice !== lastPrice) {
                            previousPriceSpan.textContent = lastPrice.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                            const priceChange = ((currentPrice - lastPrice) / lastPrice * 100).toFixed(2);
                            
                            if (currentPrice > lastPrice) {
                                priceElement.classList.remove('down');
                                priceElement.classList.add('up');
                                arrowSpan.innerHTML = '&#x2191;'; // Up arrow
                                arrowSpan.classList.remove('down');
                                arrowSpan.classList.add('up');
                                priceChangeSpan.classList.remove('down');
                                priceChangeSpan.classList.add('up');
                                priceChangeSpan.textContent = `+${priceChange}%`;
                            } else if (currentPrice < lastPrice) {
                                priceElement.classList.remove('up');
                                priceElement.classList.add('down');
                                arrowSpan.innerHTML = '&#x2193;'; // Down arrow
                                arrowSpan.classList.remove('up');
                                arrowSpan.classList.add('down');
                                priceChangeSpan.classList.remove('up');
                                priceChangeSpan.classList.add('down');
                                priceChangeSpan.textContent = `${priceChange}%`;
                            }
                        }
                        lastPrice = currentPrice;
                    }
                })
                .catch(error => {
                    console.error("Error fetching price:", error);
                });
        }

        function toggleMonitoring() {
            fetch('/toggle_monitoring')
                .then(response => response.json())
                .then(data => {
                    const button = document.getElementById('monitorButton');
                    if (data.monitoring) {
                        button.textContent = 'Stop Monitoring';
                        button.classList.add('stop');
                    } else {
                        button.textContent = 'Start Monitoring';
                        button.classList.remove('stop');
                    }
                });
        }

        // Update price every 20 seconds (3 times per minute)
        setInterval(updatePrice, 20000);
        updatePrice();
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_price')
def get_price():
    return jsonify({'price': current_btc_price})

@app.route('/toggle_monitoring')
def toggle_monitoring():
    global monitoring, monitor_thread
    
    monitoring = not monitoring
    
    if monitoring and (monitor_thread is None or not monitor_thread.is_alive()):
        monitor_thread = Thread(target=monitor_bitcoin)
        monitor_thread.daemon = True
        monitor_thread.start()
    
    return jsonify({'monitoring': monitoring})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=10000, use_reloader=False)
