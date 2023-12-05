import uuid

import psycopg2
import  config
import secrets

def get_db():
    conn=None
    curr=None
    try:
        conn = psycopg2.connect(host = config.hostname,
                            dbname=config.database,
                            user=config.username,
                            password=config.pwd,
                            port=config.port_id)
        cur = conn.cursor()
        # createval()
    except Exception as error:
        print(error)

    return conn,cur

def createval():
    conn,cur=get_db()
    active = True
    for i in range(6):
        card_id = uuid.uuid4()
        # card_id=secrets.token_hex(16)
        # print(card_id)
        bal=i+50.00
        insert_script='INSERT INTO rfid.card_detail (card_id,balance,isActive) values (%s,%s,%s)'
        insert_values=(str(card_id),bal,active)
        cur.execute(insert_script,insert_values)
        conn.commit()
        active=not active
    if cur is not None:
        cur.close()
    if conn is not None:
        conn.close()

def getrfid(rfid):
    conn, cur = get_db()
    get_script = f"SELECT * from rfid.card_detail where card_id='{rfid}'"
    # cur.execute(get_script,(rfid,))
    # cur.execute(get_script,(rfid,))
    cur.execute(get_script)

    print(cur.fetchall())
    if cur is not None:
        cur.close()
    if conn is not None:
        conn.close()

# getrfid('95e69fc5-c383-46aa-9ef3-4cb7f4f2f407')


