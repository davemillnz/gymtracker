# StrongLift Tracker

A modern web application for analyzing workout data exported from the Strong app. Upload your CSV export and instantly generate progress graphs and summaries for your lifts.

## Features

- **CSV Upload**: Drag & drop or click to upload Strong app CSV exports
- **Exercise Analysis**: Filter by specific exercises with fuzzy matching
- **Progress Graphs**: Visualize your progress over time
- **Two Analysis Modes**:
  - Best Set Mode: Shows top weight per session
  - 1RM Mode: Calculates estimated 1-rep maxes
- **Weekly Summaries**: Track workout frequency over time
- **Modern UI**: Clean, responsive design built with TailwindCSS

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Build and run with Docker
docker build -t stronglift-tracker .
docker run -p 8080:8080 stronglift-tracker
```

Then open http://localhost:8080 in your browser.

### Option 2: Local Python Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Then open http://localhost:8080 in your browser.

## API Endpoints

- `POST /api/exercises` - Get list of exercises from uploaded CSV
- `POST /api/analyze` - Analyze specific exercise and return graph data
- `POST /api/weekly-summary` - Generate weekly workout summary

## CSV Format

The application expects CSV files exported from the Strong app with these columns:
- Date
- Exercise Name  
- Weight
- Reps

## Development

This is a Flask-based web application with:
- **Backend**: Python Flask API
- **Frontend**: HTML + JavaScript with TailwindCSS
- **Charts**: Matplotlib for graph generation
- **Data Processing**: Pandas for CSV handling

## Future Features

- User authentication and accounts
- Database storage for workout history
- Personal record tracking
- Support for other fitness apps
- Social features and progress sharing

## License

MIT License
