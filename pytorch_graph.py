import matplotlib.pyplot as plt
from matplotlib import style

style.use('ggplot')

def create_acc_loss_graph(filename):
    contents = open(filename, 'r').readlines()

    times = []
    accuracies = []
    losses = []
    val_accs = []
    val_losses = []

    for c in contents:
        name, timestamp, acc, loss, val_acc, val_loss = c.split(',')
        times.append(float(timestamp))
        accuracies.append(float(acc))
        losses.append(float(loss))
        val_accs.append(float(val_acc))
        val_losses.append(float(val_loss))

    fig = plt.figure()

    ax1 = plt.subplot2grid((2,1), (0,0))
    ax2 = plt.subplot2grid((2,1), (1,0), sharex=ax1)

    ax1.plot(times, accuracies, label='acc')
    ax1.plot(times, val_accs, label = 'val_acc')
    ax1.legend(loc=2)

    ax2.plot(times, losses, label='loss')
    ax2.plot(times, val_losses, label = 'val_loss')
    ax2.legend(loc=2)

    plt.show()

    fig.savefig(filename+".png")
