import requests
import uuid

BASE_URL = "http://127.0.0.1:8000"

# --- DATA ---
PROF = {"name": "Prof. Sharma", "email": "sharma@nitj.ac.in", "password": "Password123!", "role": "professor"}
STUDENTS = [
    {"name": "Gurnaj", "email": "gurnaj@nitj.ac.in", "password": "Password123!", "role": "student", "text": "The SBERT model uses a siamese network architecture for embeddings."},
    {"name": "Amit", "email": "amit@nitj.ac.in", "password": "Password123!", "role": "student", "text": "The SBERT model uses a siamese network architecture for embeddings."} # Copied!
]

def run_demo():
    print("🚀 STARTING SEMANTIC PLAGIARISM DEMO")

    # 1. PROFESSOR SIGNUP & LOGIN
    print("\n--- [PROFESSOR SIGNUP] ---")
    requests.post(f"{BASE_URL}/auth/signup", json=PROF)
    otp = input(f"Enter OTP for {PROF['email']} from Server Terminal: ")
    requests.post(f"{BASE_URL}/auth/verify-otp", params={"email": PROF['email'], "code": otp})
    
    # LOGIN (Must use 'data=' for Form-Data)
    login_res = requests.post(f"{BASE_URL}/auth/login", data={"username": PROF['email'], "password": PROF['password']})
    prof_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {prof_token}"}

    # 2. CREATE CLASS & TASK
    c_res = requests.post(f"{BASE_URL}/classrooms/create", json={"class_name": "AI 101"}, headers=headers)
    c_id = c_res.json()["class_id"]
    t_res = requests.post(f"{BASE_URL}/classrooms/{c_id}/tasks", json={"title": "NLP Research"}, headers=headers)
    t_id = t_res.json()["task_id"]
    print(f"✅ Created Task ID: {t_id}")

    # 3. STUDENT LOOP
    for s in STUDENTS:
        print(f"\n--- [STUDENT: {s['name']}] ---")
        requests.post(f"{BASE_URL}/auth/signup", json=s)
        otp = input(f"Enter OTP for {s['email']}: ")
        requests.post(f"{BASE_URL}/auth/verify-otp", params={"email": s['email'], "code": otp})
        
        # LOGIN
        s_login = requests.post(f"{BASE_URL}/auth/login", data={"username": s['email'], "password": s['password']})
        s_token = s_login.json()["access_token"]
        s_headers = {"Authorization": f"Bearer {s_token}"}

        # SUBMIT
        files = {'file': ('assignment.pdf', s['text'], 'application/pdf')}
        sub_res = requests.post(f"{BASE_URL}/assignments/submit/{t_id}", files=files, headers=s_headers)
        print(f"📊 Result: {sub_res.json().get('plagiarism_score')}")

    # 4. FINAL REVEAL
    print("\n--- [FINAL COLLUSION REPORT] ---")
    final = requests.get(f"{BASE_URL}/assignments/collusion-groups/{t_id}", headers=headers)
    print(f"🕸️ Cheating Groups Found: {final.json().get('groups')}")

if __name__ == "__main__":
    run_demo()