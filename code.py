

import numpy as np
import torch 
import torch.nn as nn
import pandas as pd
import matplotlib.pyplot as plt
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
class RNN(nn.Module):
  def __init__(self, input_size, output_size, hidden_dim, n_layers,dropout_prob=0.5):
    super(RNN, self).__init__()

    self.hidden_dim = hidden_dim
    self.n_layers = n_layers

    self.rnn = nn.RNN(input_size, hidden_dim, n_layers, batch_first=True,dropout=dropout_prob)
    self.fc = nn.Linear(hidden_dim, output_size)
    self.batchnorm = nn.BatchNorm1d(hidden_dim)

  def forward(self, x):
    batch_size = x.size(0)

    hidden = (torch.zeros(self.n_layers, batch_size, self.hidden_dim)).to(device)

    output, hidden = self.rnn(x, hidden)
    output = self.fc(output.contiguous().view(-1, self.hidden_dim))

    return output, hidden
def train(model, optimizer, criterion, train_loader,test_loader, epochs):
  model = model.to(device)

  train_loss = []
  test_loss = []

  for epoch in range(epochs):
    model.train()
    for i, (input, label) in enumerate(train_loader):
      input = input.to(device)
      label = label.to(device)
      
      optimizer.zero_grad()
      output, hidden = model(input)
      loss = criterion(output, label.view(-1).long())
      loss.backward()
      torch.nn.utils.clip_grad_norm_(model.parameters(), 0.25)
      optimizer.step()

      if (i+1) % 1000 == 0:
        train_loss.append(loss.item())
      if (i+1) % 10000 == 0:
        print(f"Epoch: {epoch+1}/{epochs}, loss: {loss.item()}")
    model.eval()
    with torch.no_grad():
      correct, total = 0, 0
      for i, (input, target) in enumerate(test_loader):
        input = input.to(device)
        label = label.to(device)
        output, _ = model(input)
        loss = criterion(output, label.view(-1).long())

    
    test_loss.append(loss.item())
    print('Test loss : ',loss.item())
  return train_loss, test_loss
def plot(train_loss,test_loss,epochs):

  plt.plot(range(epochs*10), train_loss)
  plt.xlabel('updates(thousand)')
  plt.title('Training Loss per 1000 updates')
  plt.show()
  plt.plot(range(epochs), test_loss)
  plt.xlabel('updates(thousand)')
  plt.title('Testing Loss per 1000 updates')
  plt.show()
def new_sentence(model, word,char_map_int,unq_chars):
  new=[]
  
  for each in word:
      new.append(each)

  sentence_len=100

  for i in range(sentence_len):
    #Initializing 
    new_ind=[[]]

    #Converting each character to its numerical counterpart using the char_map_int dictionary
    for each in new:
        new_ind[0].append(char_map_int[each])

    ind=np.array(new_ind)

    #One-hot encoding the array
    embed = np.zeros((1, ind.shape[1], 82), dtype=np.float32)
  
    for j in range(ind.shape[1]):
      embed[0, j, ind[0][j]] = 1
    ind=embed

    
    ind = torch.from_numpy(ind).to(device)

    #Predicting
    output, hidden = model(ind)

    indices= torch.max(nn.functional.softmax(output[-1], dim=0).data, dim=0)[1].item()

    new.append(dict(enumerate(unq_chars))[indices])

  return ''.join(new)
def main():
  #Reading the file
  path = '/content/book-war-and-peace.txt'
  myFile=open (path, 'r')
  text = open(path, 'r').read()

  #Creating a char to int dictionary
  unq_chars = set(''.join(text))
  char_map_int = dict(zip(unq_chars , range(len(unq_chars))))

  #converting the text to numbers for one-hot encoding
  def convert_to_int(text):
    new_text=[]
    for i in text:
      new_text.append(char_map_int[i])
    return new_text

  train_input = []
  train_label = []
  test_input=[]
  test_label=[]
  for i in range(10000):
    train_input.append(convert_to_int(text[i:i+25]))
    train_label.append(convert_to_int(text[i+1:i+26]))
    test_input.append(convert_to_int(text[10000+i:10000+i+25]))
    test_label.append(convert_to_int(text[10000+i+1:10000+i+26]))


  #One hot encoding of both train and test set
  input_embedded_train = np.zeros((10000,25,82), dtype=np.float32)
  for i in range(10000):
    for j in range(25):
      input_embedded_train[i, j, train_input[i][j]] = 1

  input_embedded_test = np.zeros((10000,25,82), dtype=np.float32)
  for i in range(10000):
    for j in range(25):
      input_embedded_test[i, j, test_input[i][j]] = 1

  input_embedded_train=torch.from_numpy(input_embedded_train)
  train_label = torch.Tensor(train_label)
  input_embedded_test=torch.from_numpy(input_embedded_test)
  test_label = torch.Tensor(train_label)


  trainset = torch.utils.data.TensorDataset(input_embedded_train, train_label)
  train_loader = torch.utils.data.DataLoader(trainset, batch_size=1, shuffle=True)

  testset = torch.utils.data.TensorDataset(input_embedded_test, test_label)
  test_loader = torch.utils.data.DataLoader(testset, batch_size=1, shuffle=True)

  model =(RNN(input_size=82, output_size=82, hidden_dim=180, n_layers=1,dropout_prob=0.4)).to(device)
  # weight_decay = 0.000001
  criterion = nn.CrossEntropyLoss()
  epochs=15
  optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
  train_loss, test_loss = train(model, optimizer, nn.CrossEntropyLoss(), train_loader,test_loader, epochs)
  torch.save(model.state_dict(), "model_RNN.pth")
  model.load_state_dict(torch.load("model_RNN.pth",map_location=device))

  plot(train_loss,test_loss,epochs)
  new_sentence(model, 'have',char_map_int,unq_chars)

if __name__=="__main__":
  main()
