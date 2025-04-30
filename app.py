# app.py
from flask import Flask, render_template_string, request
import os

app = Flask(__name__)

# HTML Template with embedded CSS and JS
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Percentage Calculator</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #f8f9fa;
            padding: 20px;
        }
        .calculator-container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        .calculator-header {
            text-align: center;
            margin-bottom: 30px;
            color: #0d6efd;
        }
        .form-control, .form-select {
            border-radius: 8px;
            padding: 12px 15px;
            margin-bottom: 15px;
        }
        .btn-calculate {
            background-color: #0d6efd;
            border: none;
            padding: 12px;
            font-weight: 600;
            width: 100%;
            border-radius: 8px;
        }
        .result-container {
            margin-top: 25px;
            padding: 15px;
            border-radius: 8px;
            background-color: #f8f9fa;
            display: {% if result is not none %}block{% else %}none{% endif %};
        }
        .operation-explanation {
            font-size: 0.9em;
            color: #6c757d;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="calculator-container">
        <h1 class="calculator-header">Percentage Calculator</h1>
        
        <form method="POST" action="/">
            <div class="mb-3">
                <label for="number" class="form-label">Number</label>
                <input type="number" step="any" class="form-control" id="number" name="number" required
                       value="{{ request.form.get('number', '') }}">
            </div>
            
            <div class="mb-3">
                <label for="percent" class="form-label">Percentage</label>
                <input type="number" step="any" class="form-control" id="percent" name="percent" required
                       value="{{ request.form.get('percent', '') }}">
            </div>
            
            <div class="mb-3">
                <label class="form-label">Operation</label>
                <select class="form-select" name="operation" id="operation">
                    <option value="of" {% if request.form.get('operation') == 'of' %}selected{% endif %}>What is X% of Y?</option>
                    <option value="what" {% if request.form.get('operation') == 'what' %}selected{% endif %}>X is what % of Y?</option>
                    <option value="increase" {% if request.form.get('operation') == 'increase' %}selected{% endif %}>Increase X by Y%</option>
                    <option value="decrease" {% if request.form.get('operation') == 'decrease' %}selected{% endif %}>Decrease X by Y%</option>
                </select>
                <div class="operation-explanation" id="operation-explanation">
                    {% if request.form.get('operation') == 'of' %}
                        Calculates what X percent of Y is
                    {% elif request.form.get('operation') == 'what' %}
                        Calculates what percentage X is of Y
                    {% elif request.form.get('operation') == 'increase' %}
                        Increases X by Y percent
                    {% elif request.form.get('operation') == 'decrease' %}
                        Decreases X by Y percent
                    {% else %}
                        Select an operation to see explanation
                    {% endif %}
                </div>
            </div>
            
            <button type="submit" class="btn btn-primary btn-calculate">Calculate</button>
        </form>
        
        {% if result is not none %}
        <div class="result-container">
            <h4>Result</h4>
            <p class="mb-0">{{ result }}</p>
        </div>
        {% endif %}
    </div>

    <!-- Bootstrap 5 JS Bundle with Popper -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        // Update operation explanation when selection changes
        document.getElementById('operation').addEventListener('change', function() {
            const explanations = {
                'of': 'Calculates what X percent of Y is',
                'what': 'Calculates what percentage X is of Y',
                'increase': 'Increases X by Y percent',
                'decrease': 'Decreases X by Y percent'
            };
            document.getElementById('operation-explanation').textContent = explanations[this.value];
        });
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        try:
            number = float(request.form['number'])
            percent = float(request.form['percent'])
            operation = request.form['operation']
            
            if operation == 'of':
                calculation = (number * percent) / 100
                result = f"{percent}% of {number} = {round(calculation, 2)}"
            elif operation == 'what':
                calculation = (percent / number) * 100
                result = f"{percent} is {round(calculation, 2)}% of {number}"
            elif operation == 'increase':
                calculation = number * (1 + percent/100)
                result = f"{number} increased by {percent}% = {round(calculation, 2)}"
            elif operation == 'decrease':
                calculation = number * (1 - percent/100)
                result = f"{number} decreased by {percent}% = {round(calculation, 2)}"
        except ValueError:
            result = "Error: Please enter valid numbers"
    
    return render_template_string(HTML_TEMPLATE, result=result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)