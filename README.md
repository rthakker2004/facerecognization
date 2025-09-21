Face Voting App (ArcFace via InsightFace)\n\nSee requirements.txt for pinned versions.\nRun: python -m venv venv; source venv/bin/activate; pip install -r requirements.txt; python app.py\n

https://chatgpt.com/share/68c6ba47-668c-8011-8125-d96a0f51616c

Install Python 3.10 (model requires python 3.10)
# 1) Use Python 3.10 to create venv (run from project folder) 
py -3.10 -m venv venv

# 2) Activate the venv
.\venv\Scripts\Activate

# 3) Upgrade pip/setuptools/wheel first (important)
python -m pip install --upgrade pip setuptools wheel

# 4) Install a NumPy version compatible with the prebuilt insightface wheel
python -m pip install numpy==1.24.3

# 5) Install insightface from the team's wheel index (avoids compiling C extensions)
python -m pip install insightface==0.7.3 -f https://insightface.ai/wheels

# 6) Install onnxruntime (insightface depends on it)
python -m pip install onnxruntime==1.20.0

# 7) Install the web and image libs your app needs
python -m pip install Flask==2.2.5 opencv-python==4.7.0.72 scikit-learn==1.2.2 Pillow==9.5.0

# 8) If you have other entries in requirements.txt you still want, install them WITHOUT re-resolving deps
#    (this avoids pip trying to rebuild insightface). Adjust path if needed.
python -m pip install -r requirements.txt --no-deps

# 9) (Optional) If you ever see the "numpy.dtype size changed" error, force-reinstall the chosen numpy:
# python -m pip install --force-reinstall numpy==1.24.3

# 10) Run the app
python app.py
