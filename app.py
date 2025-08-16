from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from datetime import datetime
import json
import os
import tempfile
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def estimate_1rm(weight, reps):
    """Epley formula for 1RM estimation."""
    return weight * (1 + reps / 30.0)

def list_exercises(df):
    """Return list of available exercises."""
    return sorted(df["Exercise Name"].dropna().unique().tolist())

def resolve_exercise_name(df, query):
    """Resolve exercise name with fuzzy matching."""
    all_exercises = df["Exercise Name"].dropna().unique()

    # Exact (case-insensitive)
    exact = [ex for ex in all_exercises if ex.lower() == query.lower()]
    if exact:
        return exact[0]

    # Partial (case-insensitive)
    part = [ex for ex in all_exercises if query.lower() in ex.lower()]
    if len(part) == 1:
        return part[0]
    if len(part) > 1:
        return {"error": f"Multiple matches found: {', '.join(part)}"}
    
    return {"error": f"No matches found for '{query}'"}

def best_set_per_day(df_one_ex):
    """Return one best set per calendar day (max weight, then reps)."""
    ranked = df_one_ex.sort_values(["Weight", "Reps"], ascending=[False, False])
    # one row per day
    best = ranked.groupby("Date", as_index=False).first()
    # Ensure clean dtypes
    best["Reps"] = best["Reps"].astype(int)
    return best[["Date", "Weight", "Reps"]].sort_values("Date")

def running_best(series):
    """Monotonic non-decreasing running max."""
    out = []
    current = float("-inf")
    for v in series:
        current = max(current, v)
        out.append(current)
    return out

def calculate_prs(df_exercise):
    """Calculate personal records for an exercise."""
    if len(df_exercise) == 0:
        return {}
    
    # Ensure we have valid data
    df_valid = df_exercise[(df_exercise["Weight"] > 0) & (df_exercise["Reps"] > 0)].copy()
    
    if len(df_valid) == 0:
        return {}
    
    # Calculate 1RM for each set
    df_valid["1RM"] = df_valid.apply(lambda r: estimate_1rm(r["Weight"], r["Reps"]), axis=1)
    
    # Find highest 1RM
    max_1rm_row = df_valid.loc[df_valid["1RM"].idxmax()]
    pr_1rm = {
        "value": round(max_1rm_row["1RM"], 1),
        "weight": max_1rm_row["Weight"],
        "reps": max_1rm_row["Reps"],
        "date": max_1rm_row["Date"]
    }
    
    # Find highest weight (prioritizing higher reps for same weight)
    # Sort by weight descending, then by reps descending
    df_valid_sorted = df_valid.sort_values(["Weight", "Reps"], ascending=[False, False])
    max_weight_row = df_valid_sorted.iloc[0]
    pr_highest_weight = {
        "weight": max_weight_row["Weight"],
        "reps": max_weight_row["Reps"],
        "date": max_weight_row["Date"]
    }
    
    # Find highest volume
    df_valid["Volume"] = df_valid["Weight"] * df_valid["Reps"]
    max_volume_row = df_valid.loc[df_valid["Volume"].idxmax()]
    pr_volume = {
        "value": int(max_volume_row["Volume"]),
        "weight": max_volume_row["Weight"],
        "reps": max_volume_row["Reps"],
        "date": max_volume_row["Date"]
    }
    
    return {
        "1rm": pr_1rm,
        "highest_weight": pr_highest_weight,
        "volume": pr_volume
    }

def generate_graph_data(best, exercise_name, analysis_mode='weight'):
    """Generate graph data and create matplotlib plot."""
    # Compute value column based on analysis mode
    if analysis_mode == '1rm':
        best["Value"] = best.apply(lambda r: estimate_1rm(r["Weight"], r["Reps"]), axis=1)
        y_label = "1RM (kg, est.)"
        line_label = "Session 1RM (est.)"
        title_suffix = " (1RM est.)"
    elif analysis_mode == 'volume':
        best["Value"] = best.apply(lambda r: r["Weight"] * r["Reps"], axis=1)
        y_label = "Volume (kg × reps)"
        line_label = "Session best volume"
        title_suffix = " (Volume)"
    else:  # Default to weight mode
        best["Value"] = best["Weight"].astype(float)
        y_label = "Weight (kg)"
        line_label = "Session best weight"
        title_suffix = ""

    # Running PR line (never down)
    best["BestSoFar"] = running_best(best["Value"].tolist())

    # Convert dates to strings for JSON serialization
    dates = [d.isoformat() if hasattr(d, 'isoformat') else str(d) for d in best["Date"].tolist()]
    values = best["Value"].tolist()
    pr_line = best["BestSoFar"].tolist()

    # Create matplotlib plot
    plt.figure(figsize=(10, 6))
    plt.plot(dates, values, marker="o", label=line_label)
    plt.plot(dates, pr_line, linestyle="--", label="All-time best so far")
    plt.fill_between(dates, pr_line, alpha=0.2)

    title = f"Best {exercise_name} per Session{title_suffix}"
    plt.title(title)
    plt.ylabel(y_label)
    plt.xlabel("Date")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()

    # Convert plot to base64 string
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
    img_buffer.seek(0)
    img_str = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()

    return {
        "graph_image": img_str,
        "data": {
            "dates": dates,
            "values": values,
            "pr_line": pr_line,
            "exercise": exercise_name,
            "analysis_mode": analysis_mode
        }
    }

@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')

@app.route('/about')
def about():
    """Serve the about page."""
    return render_template('about.html')

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Handle feedback submission and CSV upload."""
    try:
        # Get reCAPTCHA response (optional for now)
        recaptcha_response = request.form.get('g-recaptcha-response')
        
        # Try to verify reCAPTCHA if configured, but don't fail if not set up
        if recaptcha_response:
            recaptcha_secret = os.environ.get('RECAPTCHA_SECRET')
            if recaptcha_secret:
                try:
                    verify_url = "https://www.google.com/recaptcha/api/siteverify"
                    verify_data = {
                        'secret': recaptcha_secret,
                        'response': recaptcha_response
                    }
                    
                    verify_response = requests.post(verify_url, data=verify_data, timeout=10)
                    verify_result = verify_response.json()
                    
                    if not verify_result.get('success', False):
                        print(f"reCAPTCHA verification failed: {verify_result}")
                        # Don't block the request, just log the failure
                except Exception as e:
                    print(f"reCAPTCHA verification error: {str(e)}")
                    # Don't block the request, just log the error
        
        # Process feedback text
        feedback_message = request.form.get('message', '').strip()
        if feedback_message:
            print(f"=== USER FEEDBACK RECEIVED ===")
            print(f"Timestamp: {datetime.now().isoformat()}")
            print(f"Message: {feedback_message}")
            print(f"================================")
        
        # Process CSV file upload
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '' and file.filename.endswith('.csv'):
                try:
                    # Save to temp directory
                    temp_dir = tempfile.gettempdir()
                    temp_filename = f"feedback_csv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    temp_path = os.path.join(temp_dir, temp_filename)
                    
                    file.save(temp_path)
                    print(f"=== CSV FILE UPLOADED ===")
                    print(f"Timestamp: {datetime.now().isoformat()}")
                    print(f"Original filename: {file.filename}")
                    print(f"Saved to: {temp_path}")
                    print(f"File size: {os.path.getsize(temp_path)} bytes")
                    print(f"=========================")
                except Exception as e:
                    print(f"Error saving CSV file: {str(e)}")
                    # Don't fail the entire request, just log the error
        
        # Log that feedback was processed successfully
        print(f"Feedback processed successfully at {datetime.now().isoformat()}")
        
        return jsonify({"message": "Thanks for your feedback!"})
        
    except Exception as e:
        print(f"Error in feedback endpoint: {str(e)}")
        return jsonify({"error": f"Error processing feedback: {str(e)}"}), 500

@app.route('/api/exercises', methods=['POST'])
def get_exercises():
    """Get list of available exercises from uploaded CSV."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "File must be a CSV"}), 400

        # Read CSV
        df = pd.read_csv(file)
        
        # Basic validation
        required_columns = ["Date", "Exercise Name", "Weight", "Reps"]
        if not all(col in df.columns for col in required_columns):
            return jsonify({"error": "CSV must contain Date, Exercise Name, Weight, and Reps columns"}), 400

        # Process dates
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
        df = df.dropna(subset=["Date", "Exercise Name"])
        
        # Valid sets only
        df = df[(df["Weight"] > 0) & (df["Reps"] > 0)]
        
        exercises = list_exercises(df)
        
        return jsonify({
            "exercises": exercises,
            "total_workouts": len(df["Date"].unique()),
            "total_sets": len(df)
        })
        
    except Exception as e:
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_exercise():
    """Analyze a specific exercise and return graph data."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        exercise_name = request.form.get('exercise', '')
        analysis_mode = request.form.get('analysis_mode', 'weight')
        
        if not exercise_name:
            return jsonify({"error": "Exercise name is required"}), 400

        # Validate analysis mode
        valid_modes = ['weight', '1rm', 'volume']
        if analysis_mode not in valid_modes:
            return jsonify({"error": f"Invalid analysis mode. Must be one of: {', '.join(valid_modes)}"}), 400

        # Read CSV
        df = pd.read_csv(file)
        
        # Process dates
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
        df = df.dropna(subset=["Date", "Exercise Name"])
        
        # Valid sets only
        df = df[(df["Weight"] > 0) & (df["Reps"] > 0)]
        
        # Resolve exercise name
        resolved = resolve_exercise_name(df, exercise_name)
        if isinstance(resolved, dict) and "error" in resolved:
            return jsonify(resolved), 400
        
        chosen_exercise = resolved
        df_ex = df[df["Exercise Name"] == chosen_exercise].copy()
        
        if len(df_ex) == 0:
            return jsonify({"error": f"No data found for exercise: {chosen_exercise}"}), 400
        
        # Build best set per day
        best = best_set_per_day(df_ex)
        
        # Calculate personal records
        prs = calculate_prs(df_ex)
        
        # Generate graph data
        result = generate_graph_data(best, chosen_exercise, analysis_mode)
        
        # Add PRs to the result
        result["prs"] = prs
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Error analyzing exercise: {str(e)}"}), 500

@app.route('/api/weekly-summary', methods=['POST'])
def weekly_summary():
    """Generate weekly workout summary."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        
        # Read CSV
        df = pd.read_csv(file)
        
        # Process dates
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
        df = df.dropna(subset=["Date", "Exercise Name"])
        
        # Valid sets only
        df = df[(df["Weight"] > 0) & (df["Reps"] > 0)]
        
        # Group by week
        df["Week"] = pd.to_datetime(df["Date"]).dt.isocalendar().week
        df["Year"] = pd.to_datetime(df["Date"]).dt.isocalendar().year
        
        weekly_counts = df.groupby(["Year", "Week"]).size().reset_index(name="workouts")
        weekly_counts["date_range"] = weekly_counts.apply(
            lambda x: f"Week {x['Week']}, {x['Year']}", axis=1
        )
        
        return jsonify({
            "weekly_data": weekly_counts.to_dict('records')
        })
        
    except Exception as e:
        return jsonify({"error": f"Error generating weekly summary: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
