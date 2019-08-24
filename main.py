from wrap import wrap, subscribe


from machine import Pin, PWM


s1 = PWM(Pin(0), freq=50, duty=77)
s2 = PWM(Pin(2), freq=50, duty=77)


@subscribe('servo_1')
def on_servo_1(message):
    print(message)

    try:
        s1.duty(int(message))
    except Exception as e:
        print(e)


@subscribe('servo_2')
def on_servo_2(message):
    print(message)
    try:
        s2.duty(int(message))
    except:
        pass


async def main():
    pass


wrap(main, "config.json")
