// GymTracker Frontend JavaScript

class GymTracker {
    constructor() {
        this.currentFile = null;
        this.exercises = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
    }

    setupEventListeners() {
        // File input change for both mobile and desktop
        document.getElementById('fileInput').addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files[0]);
        });
        
        document.getElementById('fileInputMobile').addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files[0]);
        });

        // Analyze button
        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.analyzeExercise();
        });

        // Exercise selection change
        document.getElementById('exerciseSelect').addEventListener('change', (e) => {
            this.toggleAnalyzeButton();
        });
    }

    setupDragAndDrop() {
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');

        // Only set up drag and drop on desktop devices
        if (!this.isMobileDevice()) {
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('dragover');
            });

            dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                dropZone.classList.remove('dragover');
            });

            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleFileSelect(files[0]);
                }
            });

            // Click to upload (desktop only)
            dropZone.addEventListener('click', () => {
                fileInput.click();
            });
        }
    }

    isMobileDevice() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               (window.innerWidth <= 768);
    }

    async handleFileSelect(file) {
        if (!file) return;

        // Clear any previous error messages
        this.hideError();

        if (!file.name.endsWith('.csv')) {
            this.showError('Please select a CSV file.');
            return;
        }

        if (file.size > 10 * 1024 * 1024) { // 10MB limit
            this.showError('File size must be less than 10MB.');
            return;
        }

        this.currentFile = file;
        this.showLoading('Processing CSV file...');

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/exercises', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                this.exercises = data.exercises;
                this.populateExerciseSelect();
                this.showFileInfo(data);
                this.showExerciseSection();
                this.hideLoading();
                
                // Show success message for mobile users
                if (this.isMobileDevice()) {
                    this.showSuccess(`File uploaded successfully! Found ${data.exercises.length} exercises.`);
                }
            } else {
                throw new Error(data.error || 'Failed to process file');
            }
        } catch (error) {
            this.hideLoading();
            this.showError(`Error processing file: ${error.message}`);
        }
    }

    populateExerciseSelect() {
        const select = document.getElementById('exerciseSelect');
        select.innerHTML = '<option value="">Choose an exercise...</option>';
        
        this.exercises.forEach(exercise => {
            const option = document.createElement('option');
            option.value = exercise;
            option.textContent = exercise;
            select.appendChild(option);
        });
    }

    showFileInfo(data) {
        const fileInfo = document.getElementById('fileInfo');
        const fileStats = document.getElementById('fileStats');

        fileStats.innerHTML = `
            <div class="bg-blue-50 p-4 rounded-lg">
                <h4 class="font-semibold text-blue-900">Total Exercises</h4>
                <p class="text-2xl font-bold text-blue-600">${data.exercises.length}</p>
            </div>
            <div class="bg-green-50 p-4 rounded-lg">
                <h4 class="font-semibold text-green-900">Total Workouts</h4>
                <p class="text-2xl font-bold text-green-600">${data.total_workouts}</p>
            </div>
            <div class="bg-purple-50 p-4 rounded-lg">
                <h4 class="font-semibold text-purple-900">Total Sets</h4>
                <p class="text-2xl font-bold text-purple-600">${data.total_sets}</p>
            </div>
        `;

        fileInfo.classList.remove('hidden');
    }

    showExerciseSection() {
        document.getElementById('exerciseSection').classList.remove('hidden');
    }

    toggleAnalyzeButton() {
        const exercise = document.getElementById('exerciseSelect').value;
        const analyzeBtn = document.getElementById('analyzeBtn');
        analyzeBtn.disabled = !exercise;
    }

    async analyzeExercise() {
        if (!this.currentFile) return;

        const exercise = document.getElementById('exerciseSelect').value;
        const use1rm = document.querySelector('input[name="analysisMode"]:checked').value === '1rm';

        if (!exercise) {
            this.showError('Please select an exercise.');
            return;
        }

        this.showLoading('Analyzing exercise...');

        try {
            const formData = new FormData();
            formData.append('file', this.currentFile);
            formData.append('exercise', exercise);
            formData.append('use_1rm', use1rm);

            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                this.displayResults(data);
                this.hideLoading();
            } else {
                throw new Error(data.error || 'Failed to analyze exercise');
            }
        } catch (error) {
            this.hideLoading();
            this.showError(`Error analyzing exercise: ${error.message}`);
        }
    }

    displayResults(data) {
        const resultsSection = document.getElementById('resultsSection');
        const graphContainer = document.getElementById('graphContainer');

        // Display the graph image
        graphContainer.innerHTML = `
            <div class="graph-container">
                <h4 class="text-lg font-semibold mb-4">${data.data.exercise} Progress</h4>
                <img src="data:image/png;base64,${data.graph_image}" 
                     alt="Exercise Progress Graph" 
                     class="max-w-full h-auto mx-auto">
                <div class="mt-4 text-sm text-gray-600">
                    <p>Analysis Mode: ${data.data.use_1rm ? '1RM Estimate' : 'Best Set'}</p>
                    <p>Data Points: ${data.data.dates.length}</p>
                </div>
            </div>
        `;

        resultsSection.classList.remove('hidden');
    }

    showLoading(message) {
        // Create or update loading indicator
        let loading = document.getElementById('loading');
        if (!loading) {
            loading = document.createElement('div');
            loading.id = 'loading';
            loading.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
            loading.innerHTML = `
                <div class="bg-white p-6 rounded-lg shadow-xl text-center">
                    <div class="loading-spinner mx-auto mb-4"></div>
                    <p class="text-gray-700">${message}</p>
                </div>
            `;
            document.body.appendChild(loading);
        } else {
            loading.querySelector('p').textContent = message;
        }
    }

    hideLoading() {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.remove();
        }
    }

    showError(message) {
        // Create error notification
        const error = document.createElement('div');
        error.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
        error.textContent = message;
        
        document.body.appendChild(error);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            error.remove();
        }, 5000);
    }

    showSuccess(message) {
        const success = document.createElement('div');
        success.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
        success.textContent = message;
        document.body.appendChild(success);

        setTimeout(() => {
            success.remove();
        }, 5000);
    }

    hideError() {
        const error = document.querySelector('.fixed.top-4.right-4.bg-red-500');
        if (error) {
            error.remove();
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new GymTracker();
});
