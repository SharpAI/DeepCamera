import face_detection as m
import time

benchmark=[
    {'res':480,'file':'./1_854x480.jpg','minsize':40,'cpus':1,'result':0},
    {'res':1080,'file':'./1_1920x1080.jpg','minsize':80,'cpus':1,'result':0},
    {'res':1080,'file':'./1_1920x1080.jpg','minsize':200,'cpus':1,'result':0},
        {'res':480,'file':'./1_854x480.jpg','minsize':40,'cpus':2,'result':0},
        {'res':1080,'file':'./1_1920x1080.jpg','minsize':80,'cpus':2,'result':0},
        {'res':1080,'file':'./1_1920x1080.jpg','minsize':200,'cpus':2,'result':0}
]


m.init('./model/')
print('warming up')
m.set_minsize(40)
m.set_num_threads(1)
m.set_threshold(0.6,0.7,0.8)
result = m.detect('./1_854x480.jpg')
print(result)
m.detect('./1_854x480.jpg')
m.detect('./1_854x480.jpg')
m.detect('./1_854x480.jpg')
m.detect('./1_854x480.jpg')
print('starting up')

rounds=20

for item in benchmark:
    print(item)
    m.set_minsize(item['minsize'])
    m.set_num_threads(item['cpus'])
    start = time.time()
    for i in range(rounds):
      step_start = time.time()
      result = m.detect('./1_854x480.jpg')
      step_end = time.time()
      print('step {} duration is {}'.format(i,step_end - step_start))

    end = time.time()
    print(result)

    print('{}p average duration is {}'.format(item['res'],(end - start)/rounds))
    item['result'] = (end - start)/rounds
print(benchmark)
