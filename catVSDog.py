
import os
import cv2
import numpy as np
from tqdm import tqdm
import torch.optim as optim
import torch
import torch.nn as nn
import torch.nn.functional as F
import pytorch_graph

REBUILD_DATA = False # set to true once
IMG_SIZE = 100
class DogsVSCats():

    CATS = "PetImages/Cat"
    DOGS = "PetImages/Dog"
    LABELS = {CATS:0, DOGS:1}
    training_data = []
    catcount = 0
    dogcount = 0

    def make_training_data(self):
        for label in self.LABELS:
            for f in tqdm(os.listdir(label)):
                try:
                    path = os.path.join(label, f)
                    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
                    self.training_data.append([np.array(img), np.eye(2)[self.LABELS[label]]])
                    
                    if label == self.CATS:
                        self.catcount += 1
                    elif label == self.DOGS:
                        self.dogcount +=1
                    else:
                        print('!!!')
                except Exception as e:
                    pass
        np.random.shuffle(self.training_data)
        print('Cats:', self.catcount)
        print('Dogs:', self.dogcount)
        np.save('catDogTraining_data.npy', np.array(self.training_data, dtype=object))

                
if REBUILD_DATA:
    dogsVSCats = DogsVSCats()
    dogsVSCats.make_training_data()

training_data = np.load('catDogTraining_data.npy', allow_pickle=True)

# print(len(training_data))

# print(training_data[0])
# import matplotlib.pyplot as plt
# plt.imshow(training_data[0][0], cmap="gray")




class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, 5)
        self.conv2 = nn.Conv2d(32, 64, 5)
        self.conv3 = nn.Conv2d(64, 128, 5)

        x = torch.randn(IMG_SIZE,IMG_SIZE).view(-1, 1, IMG_SIZE, IMG_SIZE)
        self._to_linear = None
        self.convs(x)
        print(self._to_linear)
        
        self.fc1 = nn.Linear(self._to_linear, 512)
        self.fc2 = nn.Linear(512, 2)
    
    def convs(self, x):
        x = F.max_pool2d(F.relu(self.conv1(x)), (2,2))
        x = F.max_pool2d(F.relu(self.conv2(x)), (2,2))
        x = F.max_pool2d(F.relu(self.conv3(x)), (2,2))

        if self._to_linear is None:
            self._to_linear = x[0].shape[0] * x[0].shape[1] * x[0].shape[2]
        return x

    def forward(self,x):
        x = self.convs(x)
        x = x.view(-1, self._to_linear)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return F.softmax(x, dim=1)



if torch.cuda.is_available():
    device = torch.device('cuda:0')
    print('running on the GPU')
else:
    device = torch.device('cpu')
    print('running on the CPU')


BATCH_SIZE = 100
EPOCHS = 5

X = torch.Tensor([i[0] for i in training_data]).view(-1,IMG_SIZE,IMG_SIZE)
X = X/255.0
y = torch.Tensor([i[1] for i in training_data])

VAL_PCT = 0.1
val_size = int(len(X) * VAL_PCT)
print(val_size)

train_X = X[:-val_size]
train_y = y[:-val_size]

test_X = X[-val_size:]
test_y = y[-val_size:]

print(len(train_X))
print(train_y.shape)

import time
from datetime import datetime

MODEL_NAME = f"dog_cat-{int(time.time())}"
    

net = Net().to(device)
# net.load_state_dict(torch.load("dogVSCat.pth", weights_only=True))

loss_function = nn.MSELoss()
optimizer = optim.Adam(net.parameters(), lr = 0.001)

def fwd_pass(X, y, train=False):
    if train:
        net.zero_grad()
    outputs = net(X)
    matches = [torch.argmax(i) == torch.argmax(j) for i , j in zip(outputs, y)]
    acc = matches.count(True) / len(matches)
    loss = loss_function(outputs, y)

    if train:
        loss.backward()
        optimizer.step()
    return acc, loss

def test(size = 32):
    random_start = np.random.randint(len(test_X) - size)
    
    X, y = test_X[random_start: random_start + size], test_y[random_start: random_start + size]
    with torch.no_grad():
        val_acc, val_loss = fwd_pass(X.view(-1,1,IMG_SIZE,IMG_SIZE).to(device), y.to(device))
    return val_acc, val_loss

# val_acc, val_loss = test()
# print(val_acc, 'Loss: ', val_loss)

def train():
    BATCH_SIZE = 1000
    EPOCHS = 30
    with open('model.log', 'a') as f:
        for epoch in range(EPOCHS):
            for i in tqdm(range(0, len(train_X), BATCH_SIZE)):
                batch_X = train_X[i: i+BATCH_SIZE].view(-1, 1, IMG_SIZE,IMG_SIZE).to(device)
                batch_y = train_y[i:i+BATCH_SIZE].to(device)
                acc, loss = fwd_pass(batch_X, batch_y, train=True)

                if i % BATCH_SIZE == 0:
                    val_acc, val_loss = test(size = 100)
                    f.write(f"{MODEL_NAME}, {round(time.time(), 3)}, {round(float(acc),2)}, {round(float(loss), 4)}, {round(float(val_acc), 2)},{round(float(val_loss), 2)}\n")
            print(f'epoch: {epoch}, test:', test(size=1000))
        torch.save(net.state_dict(), f"{MODEL_NAME}_EPOCH_{str(epoch)}.pth") 
train()


pytorch_graph.create_acc_loss_graph('model.log')


