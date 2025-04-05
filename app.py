from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # Enable CORS for all routes

def load_data():
    try:
        # Verify CSV exists
        csv_path = r'C:\Users\kumar\Sitare University\Sitare University\Semister-2\Data Handling in Pyhton\Week-9 Project\Github Deploy\OverStack-Data-Analysis-\top_tags_per_year.csv'
        if not os.path.exists(csv_path):
            raise FileNotFoundError("CSV file not found")
        
        df = pd.read_csv(csv_path)
        
        # Validate required columns
        required_cols = {'Year', 'Tag', 'Count'}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing columns: {missing}")
        
        # Normalize data by year:
        # For each year, sum the counts then compute each tag's percentage of that year
        df['NormalizedCount'] = df.groupby('Year')['Count'].transform(
            lambda x: (x / x.sum()) * 100
        )
        
        print("✅ Data loaded and normalized successfully")
        return df
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        # Create fallback sample data if real data fails
        fallback_data = {
            'Year': [2023, 2023, 2022],
            'Tag': ['python', 'javascript', 'python'],
            'Count': [100, 80, 90]
        }
        fallback_df = pd.DataFrame(fallback_data)
        fallback_df['NormalizedCount'] = fallback_df.groupby('Year')['Count'].transform(
            lambda x: (x / x.sum()) * 100
        )
        return fallback_df

# Load data at startup
df = load_data()

@app.route('/api/general-stats')
def general_stats():
    try:
        if df.empty:
            raise ValueError("No data available")

        return jsonify({
            'total_tags': int(df['Tag'].nunique()),
            'years_covered': f"{int(df['Year'].min())}-{int(df['Year'].max())}",
            'time_range': {
                'start': int(df['Year'].min()),
                'end': int(df['Year'].max())
            }
        })
    except Exception as e:
        print(f"Error in general_stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tag-trends')
def tag_trends():
    try:
        if df.empty:
            raise ValueError("No data available")

        # Get top 10 tags by the average of NormalizedCount
        top_tags = (
            df.groupby('Tag')['NormalizedCount']
              .mean()
              .nlargest(10)
              .index
              .tolist()
        )

        # Create pivot table using normalized values
        trends = df.pivot_table(
            index='Year',
            columns='Tag',
            values='NormalizedCount',
            fill_value=0
        )

        # Prepare response data
        response_data = {
            'labels': [str(year) for year in trends.index],
            'tags': top_tags,
            'data': {
                tag: [float(f"{count:.2f}") for count in trends[tag]]
                for tag in top_tags
            }
        }
        return jsonify(response_data)
    except Exception as e:
        print(f"Error in tag_trends: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
