import torch
from imageio import imread
from torchvision import transforms
import time

import insightface

embedder = insightface.iresnet50(pretrained=True).cuda()
embedder.eval()

for p in embedder.parameters():
    print(p.device)

mean = [0.5] * 3
std = [0.5 * 256 / 255] * 3
preprocess = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean, std)
])

face = imread('resource/sample.jpg')

tensor = preprocess(face)

use_cuda = torch.cuda.is_available()
device = torch.device("cuda" if use_cuda else "cpu")
#tensor.to(device)
with torch.no_grad():
    print('warm up')
    for i in range (1,10):
        features = embedder(tensor.unsqueeze(0).to(device))[0]
    start = time.time()
    for i in range (1,500):
        features = embedder(tensor.unsqueeze(0).to(device))[0]
        print('inference {}'.format(i))
    end = time.time()
    print('everage run time is {}'.format((end-start)/500))
    features.to(torch.device('cpu'))
    print('feature length {}'.format(len(features)))
    print(features[:5])
