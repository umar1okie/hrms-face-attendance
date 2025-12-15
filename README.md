\# HRMS Face Attendance System



A \*\*Django-based HRMS (Human Resource Management System)\*\* with \*\*face recognition–based attendance\*\*, \*\*real-time updates via WebSockets\*\*, and \*\*background processing using Celery\*\*.



This project is designed with a \*\*microservice-ready architecture\*\*, where heavy face recognition tasks can be run separately from the core backend.



---



\## 🚀 Features



\- Face-based attendance system

\- JWT authentication (REST API)

\- Real-time updates using WebSockets (Django Channels)

\- Background tasks with Celery

\- Scheduled tasks using Celery Beat

\- PostgreSQL database

\- Redis as message broker and channel layer

\- Modular service-based architecture

\- Ready for cloud deployment (Railway / VPS)



---



\## 🧠 Architecture Overview



| Component | Technology |

|--------|-----------|

Backend API | Django + DRF |

Authentication | JWT |

WebSockets | Django Channels + Daphne |

Background Tasks | Celery |

Task Scheduling | Celery Beat |

Message Broker | Redis |

Database | PostgreSQL |

Face Recognition | InsightFace (external ML service recommended) |

Frontend | React (Vite + Tailwind) |



---



\## ⚠️ Important Note (Face Recognition)



> \*\*InsightFace \& DeepFace are heavy ML libraries\*\* and are \*\*NOT recommended\*\* to run on free cloud tiers (Railway, Render).



\### Recommended Setup:

\- Run face recognition on:

&nbsp; - Local machine OR

&nbsp; - Separate VPS / ML microservice

\- Core Django backend communicates with ML service via API



---



\## 📁 Project Structure



hrms-face-attendance/

├── attendance\_ai/ # Main Django app

├── config/ # Django project configuration

├── frontend/ # React frontend

├── manage.py

├── requirements.txt # Cloud-safe dependencies

├── requirements-ml.txt # ML-only dependencies (local/VPS)

├── Procfile # Railway process definitions

└── README.md



1.Start PostgreSQL

Ensure PostgreSQL is running and the database exists.


2.Start Redis

redis-server


3.Apply Migrations

python manage.py migrate


4.Run Django Server (ASGI)

python manage.py runserver







5.Start Celery Worker

celery -A config worker -l info


6. Start Celery Beat (Scheduler)

celery -A config beat -l info

