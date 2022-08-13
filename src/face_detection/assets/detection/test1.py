import face_detection as m
import time

m.init('./model/')
m.set_minsize(100)
m.set_threshold(0.6,0.7,0.8)
m.set_num_threads(2)
print('warming up')
result = m.detect('./1_1920x1080.jpg')
print(result)
m.detect('./1_1920x1080.jpg')
m.detect('./1_1920x1080.jpg')
m.detect('./1_1920x1080.jpg')
m.detect('./1_1920x1080.jpg')

start = time.time()
for i in range(10):
  step_start = time.time()
  result = m.detect('./1_1920x1080.jpg')
  step_end = time.time()
  print('step {} duration is {}'.format(i,step_end - step_start))
end = time.time()
print(result)

print('1080p average duration is {}'.format((end - start)/10))
