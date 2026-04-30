import elevenlabs
try:
    from elevenlabs import play
    print("type of play:", type(play))
    if type(play).__name__ == 'module':
        print("play module has:", dir(play))
except Exception as e:
    print(e)
