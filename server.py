from flask import Flask, request, jsonify
import joblib
import pandas as pd
from flask_cors import CORS
import datetime
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()

app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})


# Load the pre-trained model and label encoders
model = joblib.load('model_random_forest.pkl')
label_encoders = joblib.load('label_encoders.pkl')
scaler = joblib.load('scaler.pkl')

# List of categorical columns to transform
categorical_cols =  ['fuel_type', 'brand', 'model', 'upholstery', 'gearbox', 'transmission', 'location', 'exterior_color', 'interior_color']

@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.get_json()
    print(data)
    new_data = {}
    new_data['mileage'] = data['mileage']
    new_data['year'] = data['year']
    new_data['transmission'] = data['transmission']
    new_data['gearbox'] = data['gearbox']
    new_data['fuel_type'] = data['fuel']
    new_data['location'] = data['location']
    new_data['brand'] = data['brand']
    new_data['model'] = data['model']
    new_data['exterior_color'] = data['exterior_color']
    new_data['interior_color'] = data['interior_color']
    new_data['upholstery'] = data['upholstery']
    new_data['seats'] = data['seats']
    new_data['doors'] = data['doors']
    new_data['fiscal_power'] = data['horsepower']
    # new_data['engine_fiscal_interaction']
    new_data['engine_displacement'] = data['engineDisplacement']
    new_data['age'] = datetime.datetime.now().year - int(new_data['year'])
    new_data['mileage_per_year'] = int(new_data['mileage']) / int(new_data['age'])
    new_data['seats_per_doors'] = int(new_data['seats']) / int(new_data['doors'])
    new_data['mileage_efficiency'] = int(new_data['engine_displacement']) / int(new_data['mileage'])
    new_data['engine_fiscal_interaction'] = int(new_data['engine_displacement']) * int(new_data['fiscal_power'])
    data = new_data

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    try:
        df = pd.DataFrame([data])

        numerical_cols = ['mileage', 'fiscal_power', 'engine_displacement', 'age', 'mileage_per_year', 'seats_per_doors', 'mileage_efficiency', 'engine_fiscal_interaction']
        df[numerical_cols] = scaler.transform(df[numerical_cols])

    except Exception as e:
        return jsonify({'error': f'Failed to convert data to DataFrame: {e}'}), 400


    # Transform categorical columns using the pre-saved label encoders
    try:
        for col in categorical_cols:
            if col in df.columns:
                le = label_encoders[col]
                df[col] = le.transform(df[col])
    except Exception as e:
        return jsonify({'error': f'Error encoding categorical features: {e}'}), 500
    
    # return jsonify({'data': df.to_dict(orient='records')})

    try:
        predictions = model.predict(df)
    except Exception as e:
        return jsonify({'error': f'Prediction error: {e}'}), 500

    return jsonify({'prediction': predictions.tolist()})

if __name__ == '__main__':
    app.run(debug=True)
