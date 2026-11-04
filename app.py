
import os, csv, io
from datetime import date
from functools import wraps
import psycopg
from psycopg.rows import dict_row
from flask import Flask, request, redirect, url_for, session, flash, render_template, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import mm

app=Flask(__name__); app.secret_key=os.getenv("SECRET_KEY","change-this-secret")
DATABASE_URL=os.getenv("DATABASE_URL","")
TIMETABLE={
"ND1":[
("Monday","09:00","12:00","Statistics for Computing I","COM 114","Mr Abdullahi"),("Monday","13:00","15:00","Computer Studies","COM 112","Mr Adenuga"),("Monday","15:00","17:00","Computer Studies","COM 113","Mr Abdullahi"),
("Tuesday","09:00","11:00","Use of English","GNS 101","Mr Oyedokun"),("Tuesday","11:00","12:00","Computer Studies","COM 115","Mr Adenuga"),("Tuesday","13:00","15:00","Computer Studies","COM 115","Mr Adenuga"),("Tuesday","15:00","17:00","General Studies","GNS 113","Mr Adeniran"),
("Wednesday","11:00","12:00","Computer Studies","COM 116","Mr Oyetoke"),("Wednesday","13:00","15:00","Computer Studies","COM 113","Lecturer to confirm"),("Wednesday","15:00","17:00","Computer Studies Practical","COM 113 Practical","Lecturer to confirm"),
("Thursday","09:00","12:00","Computer Studies","COM 111","Mr Adeleke"),("Thursday","13:00","15:00","Mathematics","MTH 111","Mrs Kolapo"),("Thursday","15:00","17:00","Mathematics","MTH 112","Mrs Kolapo"),
("Friday","09:00","11:00","Introduction to Psychometric Studies","Code to confirm","Mr Haastrup"),("Friday","11:00","12:00","Use of Library","LIB 111","Mr Haastrup"),("Friday","15:00","17:00","Title to confirm","SBS 101","Lecturer to confirm")],
"ND2":[
("Monday","09:00","12:00","Computer Application Package II","COM 215","Mr Adenuga"),("Monday","13:00","15:00","Computer Studies","COM 211","Mr Abdullahi"),("Monday","15:00","17:00","Practice of Entrepreneurship","EED 216","Mr Taiwo"),
("Tuesday","09:00","11:00","Computer Studies","COM 211","Mr Abdullahi"),("Tuesday","11:00","12:00","Computer Studies","COM 211","Mr Abdullahi"),("Tuesday","13:00","15:00","Computer Studies","COM 212","Mr Adeleke"),("Tuesday","15:00","17:00","Small Business Management","BUS 213","Mr Asere"),
("Wednesday","09:00","11:00","Seminar on Computer Society","COM 214","Mr Oyetoke"),("Wednesday","11:00","12:00","Computer Studies","COM 216","Mr Abdullahi"),("Wednesday","13:00","15:00","Computer Studies Practical","COM 211 Practical","Lecturer to confirm"),("Wednesday","15:00","17:00","Computer Studies Practical","COM 211 Practical","Lecturer to confirm"),
("Thursday","09:00","12:00","Computer Practical","Code to confirm","Lecturer to confirm"),("Thursday","13:00","15:00","Unified Modeling Languages (UML)","COM 213","Mrs Olufotoye"),("Thursday","15:00","17:00","Computer Studies","COM 217","Mrs Olufotoye"),
("Friday","09:00","11:00","Introduction to Psychometric Studies II","GNS 206","Mr Haastrup"),("Friday","11:00","12:00","Computer Practical","Code to confirm","Lecturer to confirm"),("Friday","13:00","14:00","Use of English II","GNS 201","Mr Oyedokun")]}
def db():
 if not DATABASE_URL:
  raise RuntimeError("DATABASE_URL is missing. Add your Supabase PostgreSQL connection string in Render Environment.")
 return psycopg.connect(DATABASE_URL, row_factory=dict_row)
def init():
 with db() as c:
  c.execute("""CREATE TABLE IF NOT EXISTS students(
   id BIGSERIAL PRIMARY KEY, level TEXT NOT NULL, student_id TEXT NOT NULL,
   full_name TEXT NOT NULL, UNIQUE(level,student_id))""")
  c.execute("""CREATE TABLE IF NOT EXISTS lessons(
   id BIGSERIAL PRIMARY KEY, level TEXT NOT NULL, day TEXT NOT NULL,
   start_time TEXT NOT NULL, end_time TEXT NOT NULL, subject TEXT NOT NULL,
   course_code TEXT NOT NULL, lecturer TEXT NOT NULL)""")
  c.execute("""CREATE TABLE IF NOT EXISTS attendance(
   id BIGSERIAL PRIMARY KEY, lesson_id BIGINT NOT NULL REFERENCES lessons(id),
   student_id BIGINT NOT NULL REFERENCES students(id), lesson_date DATE NOT NULL,
   status TEXT NOT NULL CHECK(status IN ('Present','Absent','Late')),
   UNIQUE(lesson_id,student_id,lesson_date))""")
  if c.execute("SELECT COUNT(*) AS n FROM lessons").fetchone()["n"]==0:
   for level,rows in TIMETABLE.items():
    c.executemany("INSERT INTO lessons(level,day,start_time,end_time,subject,course_code,lecturer) VALUES(%s,%s,%s,%s,%s,%s,%s)",[(level,*r) for r in rows])
def access(*roles):
 def deco(fn):
  @wraps(fn)
  def w(*a,**k):
   if session.get("role") not in roles: return redirect(url_for("login"))
   return fn(*a,**k)
  return w
 return deco
@app.route("/login",methods=["GET","POST"])
def login():
 if request.method=="POST":
  users={"admin":("admin",os.getenv("ADMIN_PASSWORD","")),"nd1_rep":("nd1",os.getenv("ND1_PASSWORD","")),"nd2_rep":("nd2",os.getenv("ND2_PASSWORD",""))}
  u=request.form.get("username","").lower().strip(); p=request.form.get("password","")
  if u in users and users[u][1] and p==users[u][1]: session.clear(); session["role"]=users[u][0]; return redirect("/")
  flash("Login failed. Check username and password.")
 return render_template("login.html")
@app.route("/logout")
def logout(): session.clear(); return redirect("/login")
@app.route("/")
@access("admin","nd1","nd2")
def home():
 if session["role"]=="admin":
  with db() as c: counts={x:c.execute("SELECT COUNT(*) AS n FROM students WHERE level=%s",(x,)).fetchone()["n"] for x in ("ND1","ND2")}; n=c.execute("SELECT COUNT(*) AS n FROM lessons").fetchone()["n"]
  return render_template("admin.html",counts=counts,n=n)
 lv="ND1" if session["role"]=="nd1" else "ND2"
 with db() as c: lessons=c.execute("SELECT * FROM lessons WHERE level=%s ORDER BY day,start_time",(lv,)).fetchall(); n=c.execute("SELECT COUNT(*) AS n FROM students WHERE level=%s",(lv,)).fetchone()["n"]
 return render_template("rep.html",level=lv,lessons=lessons,n=n)
@app.route("/students",methods=["GET","POST"])
@access("admin")
def students():
 if request.method=="POST":
  lv=request.form.get("level"); sid=request.form.get("student_id","").strip(); name=request.form.get("full_name","").strip()
  if lv in ("ND1","ND2") and sid and name:
   with db() as c: c.execute("INSERT INTO students(level,student_id,full_name) VALUES(%s,%s,%s) ON CONFLICT(level,student_id) DO UPDATE SET full_name=EXCLUDED.full_name",(lv,sid,name))
   flash("Student saved.")
  return redirect("/students")
 with db() as c: rows=c.execute("SELECT * FROM students ORDER BY level,full_name").fetchall()
 return render_template("students.html",students=rows)
@app.route("/upload",methods=["POST"])
@access("admin")
def upload():
 lv=request.form.get("level"); f=request.files.get("file")
 try:
  reader=csv.DictReader(io.StringIO(f.stream.read().decode("utf-8-sig"))); count=0
  with db() as c:
   for r in reader:
    sid=(r.get("student_id") or r.get("matric_no") or "").strip(); name=(r.get("full_name") or r.get("name") or "").strip()
    if lv in ("ND1","ND2") and sid and name: c.execute("INSERT INTO students(level,student_id,full_name) VALUES(%s,%s,%s) ON CONFLICT(level,student_id) DO UPDATE SET full_name=EXCLUDED.full_name",(lv,sid,name)); count+=1
  flash(f"Imported {count} students into {lv}.")
 except Exception: flash("Upload failed. Save Excel as CSV with student_id and full_name columns.")
 return redirect("/students")
@app.route("/timetable",methods=["GET","POST"])
@access("admin")
def timetable():
 if request.method=="POST":
  with db() as c: c.execute("UPDATE lessons SET subject=%s,course_code=%s,lecturer=%s WHERE id=%s",(request.form["subject"],request.form["course_code"],request.form["lecturer"],request.form["id"]))
  flash("Timetable updated."); return redirect("/timetable?level="+request.form["level"])
 lv=request.args.get("level","ND1")
 with db() as c: rows=c.execute("SELECT * FROM lessons WHERE level=%s ORDER BY day,start_time",(lv,)).fetchall()
 return render_template("timetable.html",lessons=rows,level=lv)
@app.route("/attendance/<int:lid>",methods=["GET","POST"])
@access("nd1","nd2")
def attendance(lid):
 lv="ND1" if session["role"]=="nd1" else "ND2"
 with db() as c:
  lesson=c.execute("SELECT * FROM lessons WHERE id=%s AND level=%s",(lid,lv)).fetchone()
  if not lesson: return redirect("/")
  students=c.execute("SELECT * FROM students WHERE level=%s ORDER BY full_name",(lv,)).fetchall(); day=request.values.get("lesson_date",date.today().isoformat())
  if request.method=="POST":
   for s in students:
    status=request.form.get("s"+str(s["id"]))
    if status in ("Present","Absent","Late"): c.execute("INSERT INTO attendance(lesson_id,student_id,lesson_date,status) VALUES(%s,%s,%s,%s) ON CONFLICT(lesson_id,student_id,lesson_date) DO UPDATE SET status=EXCLUDED.status",(lid,s["id"],day,status))
   flash("Attendance saved."); return redirect(url_for("attendance",lid=lid,lesson_date=day))
  old={r["student_id"]:r["status"] for r in c.execute("SELECT student_id,status FROM attendance WHERE lesson_id=%s AND lesson_date=%s",(lid,day))}
 return render_template("attendance.html",lesson=lesson,students=students,day=day,old=old)
@app.route("/reports")
@access("admin")
def reports(): return render_template("reports.html")
@app.route("/report.pdf")
@access("admin")
def pdf():
 lv=request.args.get("level","ND1"); code=request.args.get("course_code","").strip(); out=io.BytesIO()
 doc=SimpleDocTemplate(out,pagesize=landscape(A4),rightMargin=10*mm,leftMargin=10*mm)
 styles=getSampleStyleSheet(); story=[Paragraph("SOTERIA BUSINESS SCHOOL",styles["Title"]),Paragraph("COMPUTER SCIENCE — 2026/2027 FIRST SEMESTER ATTENDANCE",styles["Heading2"]),Paragraph(lv+" | "+(code or "All subjects"),styles["Normal"]),Spacer(1,5*mm)]
 with db() as c:
  students=c.execute("SELECT * FROM students WHERE level=%s ORDER BY full_name",(lv,)).fetchall()
  dates=[r["lesson_date"] for r in c.execute("SELECT DISTINCT a.lesson_date::text AS lesson_date FROM attendance a JOIN lessons l ON a.lesson_id=l.id WHERE l.level=%s AND (%s='' OR l.course_code=%s) ORDER BY a.lesson_date",(lv,code,code))]
  dates=dates or ["No records"]; data=[["Student ID","Student name"]+dates+["Present","Absent","Late"]]
  for s in students:
   marks=[]; totals={"Present":0,"Absent":0,"Late":0}
   for d in dates:
    vals=[] if d=="No records" else c.execute("SELECT a.status FROM attendance a JOIN lessons l ON a.lesson_id=l.id WHERE a.student_id=%s AND a.lesson_date=%s AND l.level=%s AND (%s='' OR l.course_code=%s)",(s["id"],d,lv,code,code)).fetchall()
    marks.append(", ".join(x["status"][0] for x in vals) if vals else "—")
    for x in vals: totals[x["status"]]+=1
   data.append([s["student_id"],s["full_name"]]+marks+[str(totals["Present"]),str(totals["Absent"]),str(totals["Late"])])
 widths=[27*mm,48*mm]+[17*mm]*len(dates)+[15*mm]*3; table=Table(data,repeatRows=1,colWidths=widths)
 table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#17324d")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.4,colors.grey),("FONTSIZE",(0,0),(-1,-1),7)]))
 story += [table,Spacer(1,8*mm),Paragraph("Lecturer signature: __________________________ Date: __________",styles["Normal"]),Spacer(1,5*mm),Paragraph("School administrator signature: _______________ Date: __________",styles["Normal"])]
 doc.build(story); out.seek(0); return send_file(out,as_attachment=True,download_name=f"{lv}_{code or 'all'}_attendance.pdf",mimetype="application/pdf")
init()

if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.getenv("PORT",5000)))
