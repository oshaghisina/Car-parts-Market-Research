# 🌐 Torob Scraper Web Interface

A modern, user-friendly web interface for the Torob automotive parts price scraper.

## 🚀 Features

### **Web Interface**
- **Modern UI**: Clean, responsive design with Bootstrap 5
- **File Upload**: Upload CSV files with parts data
- **Manual Entry**: Enter parts manually through the web form
- **Real-time Progress**: Live progress tracking with progress bars
- **Results Download**: Download Excel files directly from the browser
- **Task Management**: View and manage scraping tasks
- **Configuration Display**: View current scraper settings

### **Technical Features**
- **Flask Backend**: Lightweight Python web framework
- **RESTful API**: Clean API endpoints for all operations
- **Background Processing**: Scraping runs in background threads
- **File Management**: Automatic file upload and result handling
- **Error Handling**: Comprehensive error handling and user feedback
- **Responsive Design**: Works on desktop, tablet, and mobile

## 📋 Prerequisites

- Python 3.8+
- All dependencies from `requirements.txt`
- Web browser (Chrome, Firefox, Safari, Edge)

## 🛠️ Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright Browsers**:
   ```bash
   playwright install
   ```

3. **Start the Web Server**:
   ```bash
   python3 web_app.py
   ```

4. **Access the Interface**:
   Open your browser and go to: `http://localhost:5000`

## 🎯 Usage

### **1. Main Interface**
- **Upload File**: Click "Choose File" to upload a CSV file with parts data
- **Manual Entry**: Enter parts manually using the form
- **Start Scraping**: Click "Start Scraping" to begin the process

### **2. File Upload Format**
Create a CSV file with the following columns:
```csv
part_name,part_code,keywords
چراغ سمت راست تیگو ۸ پرو,TIGGO8-HEADLIGHT-RH,چراغ سمت راست تیگو ۸ پرو automotive part
چراغ سمت چپ تیگو ۸ پرو,TIGGO8-HEADLIGHT-LH,چراغ سمت چپ تیگو ۸ پرو automotive part
```

### **3. Manual Entry**
- **Part Name**: Required field for the automotive part name
- **Part Code**: Optional OEM or part number
- **Keywords**: Optional search keywords (auto-generated if empty)
- **Excel Filename**: Name for the output Excel file

### **4. Progress Tracking**
- **Real-time Updates**: Progress bar shows current status
- **Task Details**: View completed, failed, and total tasks
- **ETA**: Estimated time remaining for completion

### **5. Results**
- **Download Excel**: Click to download the results file
- **Statistics**: View scraping statistics and metrics
- **New Scraping**: Start a new scraping session

## 🔧 API Endpoints

### **Main Pages**
- `GET /` - Main interface
- `GET /api/config` - Get configuration
- `GET /api/tasks` - List all tasks

### **File Operations**
- `POST /api/upload` - Upload CSV file
- `GET /api/download/<task_id>` - Download results

### **Scraping Operations**
- `POST /api/start_scraping` - Start scraping task
- `GET /api/task_status/<task_id>` - Get task status
- `POST /api/clear_tasks` - Clear completed tasks

## 📁 File Structure

```
torob_scraper/
├── web_app.py              # Flask web application
├── templates/
│   ├── base.html           # Base template
│   └── index.html          # Main page template
├── static/
│   ├── style.css           # Custom CSS
│   └── script.js           # JavaScript functionality
├── uploads/                # Uploaded files
├── results/                # Generated Excel files
└── cache/                  # Caching directory
```

## ⚙️ Configuration

The web interface uses the same `config.yaml` file as the CLI version:

```yaml
# Web Interface Settings
web:
  host: "0.0.0.0"
  port: 5000
  debug: true
  
# File Upload Settings
upload:
  max_file_size: 10MB
  allowed_extensions: [csv, xlsx, xls]
  
# Background Processing
background:
  max_workers: 3
  timeout: 300  # 5 minutes
```

## 🚀 Advanced Usage

### **Multiple Parts Processing**
1. Select "2 Parts" or more from the dropdown
2. Fill in the part information for each part
3. Click "Start Scraping" to process all parts

### **File Upload with Validation**
1. Prepare a CSV file with the correct format
2. Upload the file using the file input
3. Review the parsed parts data
4. Start scraping with the uploaded data

### **Task Management**
1. Click "Tasks" in the navigation
2. View all running and completed tasks
3. Download results from completed tasks
4. Clear old tasks to free up space

## 🔍 Troubleshooting

### **Common Issues**

1. **Web Server Won't Start**:
   - Check if port 5000 is available
   - Ensure all dependencies are installed
   - Check for Python version compatibility

2. **File Upload Fails**:
   - Verify file format (CSV, XLSX, XLS)
   - Check file size (max 10MB)
   - Ensure file has required columns

3. **Scraping Fails**:
   - Check internet connection
   - Verify Torob.com is accessible
   - Check browser installation for Playwright

4. **Download Issues**:
   - Ensure task is completed
   - Check file permissions
   - Verify Excel file was generated

### **Debug Mode**
Start the web server in debug mode:
```bash
FLASK_DEBUG=1 python3 web_app.py
```

## 📊 Performance

### **Optimization Features**
- **Caching**: Results are cached for faster repeated searches
- **Parallel Processing**: Multiple parts processed simultaneously
- **Background Tasks**: Scraping runs in background threads
- **Progress Tracking**: Real-time progress updates

### **Resource Usage**
- **Memory**: ~100-200MB per scraping task
- **CPU**: Utilizes multiple cores for parallel processing
- **Storage**: Cached results and temporary files

## 🔒 Security

### **File Upload Security**
- File type validation
- File size limits
- Secure filename handling
- Path traversal protection

### **API Security**
- Input validation
- Error handling
- Rate limiting (configurable)
- CORS protection

## 🌟 Features Comparison

| Feature | CLI Version | Web Version |
|---------|-------------|-------------|
| **Ease of Use** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **File Upload** | ❌ | ✅ |
| **Progress Tracking** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Task Management** | ❌ | ✅ |
| **Configuration** | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Results Download** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Multi-user** | ❌ | ✅ |
| **Remote Access** | ❌ | ✅ |

## 🎉 Getting Started

1. **Start the Web Server**:
   ```bash
   python3 web_app.py
   ```

2. **Open Your Browser**:
   Go to `http://localhost:5000`

3. **Enter Part Information**:
   - Part name (required)
   - Part code (optional)
   - Keywords (optional)

4. **Start Scraping**:
   Click "Start Scraping" and watch the progress

5. **Download Results**:
   Download the Excel file when complete

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the configuration settings
3. Check the browser console for errors
4. Verify all dependencies are installed

---

**🎯 The Torob Scraper Web Interface makes automotive parts price scraping accessible to everyone!**
