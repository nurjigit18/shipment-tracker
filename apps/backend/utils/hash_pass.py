import bcrypt

pw = b'KQNOOfD8daGV9Bt2'
s = bcrypt.gensalt()

h = bcrypt.hashpw(pw, s)
print(s)
print(h)
entered_pw = b'KQNOOfD8daGV9Bt2'
if bcrypt.checkpw(entered_pw, h):
    print("Password match!")
else:
    print("Incorrect password.")