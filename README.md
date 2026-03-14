# DSMOJ-Judge
A simple judge.

# What does DSMOJ actually mean?
- On good day: Django Simple Modern Online Judge
- On bad day: Dumbass Simple Modern Online Judge
# Why is it "simple"?
You could just pull it and run it, no problem!
There's no Redis or Celery, the DB is your Celery, and there's an API endpoint to serve submissions to the judge and to update results of a submission!
# To-do list:
- [ ] Add WebSocket to frontend
- [ ] Shield server from family drama
- [ ] Add authentication to Judge API
- [ ] Make more APIs