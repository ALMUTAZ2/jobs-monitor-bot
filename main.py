  import requests
  from bs4 import BeautifulSoup
  import time
  import json
  import os
  from datetime import datetime
  import logging
  from flask import Flask

  # إنشاء تطبيق Flask (مطلوب لـ Railway)
  app = Flask(__name__)

  # إعداد التسجيل
  logging.basicConfig(
      level=logging.INFO,
      format='%(asctime)s - %(levelname)s - %(message)s'
  )

  # تكوين المتغيرات الأساسية
  TELEGRAM_TOKEN = "7762932301:AAHkbmxRKhvjeKV9uJNfh8t382cO0Ty7i2M"
  CHAT_ID = "521974594"
  URL = "https://careers.moenergy.gov.sa/ar/job-search-results/"
  
  # ملف لتخزين الوظائف السابقة
  JOBS_FILE = "previous_jobs.json"

  def get_jobs():
      """استخراج الوظائف من الموقع"""
      try:
          headers = {
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
          }
          response = requests.get(URL, headers=headers, timeout=30)
          soup = BeautifulSoup(response.content, 'html.parser')
          
          jobs = []
          job_listings = soup.find_all('div', class_='job-listing')
          
          for job in job_listings:
              title = job.find('h2').text.strip()
              link = job.find('a')['href']
              jobs.append({
                  'title': title,
                  'link': link
              })
          
          logging.info(f"تم العثور على {len(jobs)} وظيفة")
          return jobs
      except Exception as e:
          logging.error(f"خطأ في استخراج الوظائف: {str(e)}")
          return []

  def send_telegram_message(message):
      """إرسال رسالة إلى تيليجرام"""
      telegram_api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
      try:
          response = requests.post(telegram_api, data={
              "chat_id": CHAT_ID,
              "text": message,
              "parse_mode": "HTML"
          }, timeout=30)
          if response.status_code == 200:
              logging.info("تم إرسال الرسالة بنجاح")
          else:
              logging.error(f"فشل إرسال الرسالة: {response.text}")
      except Exception as e:
          logging.error(f"خطأ في إرسال الرسالة: {str(e)}")

  def load_previous_jobs():
      """تحميل الوظائف السابقة من الملف"""
      try:
          if os.path.exists(JOBS_FILE):
              with open(JOBS_FILE, 'r', encoding='utf-8') as f:
                  return json.load(f)
          return []
      except Exception as e:
          logging.error(f"خطأ في تحميل الوظائف السابقة: {str(e)}")
          return []

  def save_jobs(jobs):
      """حفظ الوظائف في الملف"""
      try:
          with open(JOBS_FILE, 'w', encoding='utf-8') as f:
              json.dump(jobs, f, ensure_ascii=False, indent=2)
          logging.info("تم حفظ الوظائف بنجاح")
      except Exception as e:
          logging.error(f"خطأ في حفظ الوظائف: {str(e)}")

  def check_jobs():
      """دالة للتحقق من الوظائف الجديدة"""
      logging.info("بدء فحص الوظائف الجديدة")
      
      current_jobs = get_jobs()
      previous_jobs = load_previous_jobs()
      new_jobs = [job for job in current_jobs if job not in previous_jobs]
      
      for job in new_jobs:
          message = f"🔔 وظيفة جديدة!\n\n"
          message += f"📌 {job['title']}\n"
          message += f"🔗 {job['link']}\n\n"
          message += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
          send_telegram_message(message)
      
      if current_jobs:
          save_jobs(current_jobs)
      
      logging.info(f"تم العثور على {len(new_jobs)} وظيفة جديدة")

  @app.route('/')
  def home():
      return 'Bot is running!'

  def run_job_checker():
      """تشغيل فاحص الوظائف بشكل دوري"""
      while True:
          check_jobs()
          time.sleep(300)  # انتظار 5 دقائق

  if __name__ == "__main__":
      # إرسال رسالة بدء التشغيل
      send_telegram_message("✅ تم بدء تشغيل بوت مراقبة الوظائف")
      
      # بدء عملية فحص الوظائف في خلفية التطبيق
      import threading
      job_thread = threading.Thread(target=run_job_checker)
      job_thread.daemon = True
      job_thread.start()
      
      # تشغيل تطبيق Flask
      port = int(os.environ.get('PORT', 5000))
      app.run(host='0.0.0.0', port=port)
