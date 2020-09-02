import face_detection as m
import time

m.init('./models/ncnn/')
print('warming up')
m.detect('./images_480p/1_854x480.jpg')
m.detect('./images_480p/1_854x480.jpg')
m.detect('./images_480p/1_854x480.jpg')
m.detect('./images_480p/1_854x480.jpg')
m.detect('./images_480p/1_854x480.jpg')

start = time.time()
for i in range(100):
  step_start = time.time()
  result = m.detect('./images_480p/1_854x480.jpg')
  step_end = time.time()
  print('step {} duration is {}'.format(i,step_end - step_start))
end = time.time()
print(result)

print('average duration is {}'.format((end - start)/100))
