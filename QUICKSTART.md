# 🚀 Quick Start Guide

## Step-by-Step Setup

### 1. Prerequisites Check

```bash
# Check Python
python3 --version  # Should be 3.8+

# Check Node.js
node --version     # Should be 16+

# Check Docker
docker --version

# Check Ollama
ollama --version
```

### 2. Run Setup Scripts

```bash
# Make scripts executable
chmod +x setup_backend.sh setup_frontend.sh setup_runner.sh

# Run in order
./setup_backend.sh
./setup_frontend.sh
./setup_runner.sh
```

### 3. Start Required Services

**Terminal 1 - Judge0:**
```bash
docker run -d -p 2358:2358 judge0/judge0:latest
```

**Terminal 2 - Ollama:**
```bash
ollama serve
```

**Terminal 3 - Pull AI Model:**
```bash
ollama pull qwen2.5-coder:3b
```

### 4. Launch Platform

```bash
./run.sh
```

### 5. Access Platform

Open your browser to: **http://localhost:5173**

## 🎮 First Steps

1. **Check Status**: Look at the top-left status indicators
   - Judge0: ✓ (green) = ready
   - AI Tutor: ✓ (green) = ready

2. **Start with Problem 1**: "Hello World"
   - Read the description
   - Write your code
   - Click "Run Code" to test
   - Click "Submit" to validate

3. **Progress**: 
   - Solve 5 beginner problems to unlock intermediate
   - Watch your score increase!
   - Get AI hints if stuck

## 🆘 Common Issues

**"Judge0 offline"**: 
```bash
docker ps  # Check if container is running
docker run -d -p 2358:2358 judge0/judge0:latest
```

**"Ollama offline"**:
```bash
# Start in new terminal
ollama serve
```

**"No output"**: Check if your code has `print()` statements

**"Tests failed"**: Compare your output with expected output carefully

## 💡 Tips

- Use "Run Code" for quick testing with sample input
- Use "Submit" to validate against all test cases
- Get AI hints only after attempting the problem
- Read problem descriptions carefully
- Check sample test cases for examples

---

**Need help?** Check the full README.md for detailed documentation.
