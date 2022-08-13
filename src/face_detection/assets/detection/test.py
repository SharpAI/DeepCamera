import face_detection as m
import time

m.init('./model/')
print('warming up')
m.set_minsize(40)
m.set_threshold(0.6,0.7,0.8)
result = m.detect('./1_854x480.jpg')
print(result)
m.detect('./1_854x480.jpg')
m.detect('./1_854x480.jpg')
m.detect('./1_854x480.jpg')
m.detect('./1_854x480.jpg')

start = time.time()
for i in range(10):
  step_start = time.time()
  result = m.detect('./1_854x480.jpg')
  step_end = time.time()
  print('step {} duration is {}'.format(i,step_end - step_start))
end = time.time()
print(result)

print('480p average duration is {}'.format((end - start)/10))
