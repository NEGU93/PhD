from mstar_data_processing import get_train_and_test
from pdb import set_trace
import numpy as np
import tensorflow as tf
import pandas as pd
import json
import pickle
import cvnn
from cvnn.utils import create_folder
from mstar_data_processing import resize_image
from mstar_utils import plot_history, create_excel_file


config = {
    'model': 'chen',
    'dtype': np.float32,
    'tensorflow': False,
    'epochs': 1,
    'batch_size': 32   # TODO: change it using tf.Dataset?
}

saver_config = {
    'add_to_excel': True,
    'model_summary': True,
    'hist_plot': True,
    'json': True
}

if config['tensorflow']:
    from tensorflow.keras.layers import Dense, Conv2D, MaxPooling2D, AveragePooling2D, Flatten, Input, Dropout
else:
    from cvnn.layers import ComplexDense as Dense
    from cvnn.layers import ComplexConv2D as Conv2D
    from cvnn.layers import ComplexMaxPooling2D as MaxPooling2D
    from cvnn.layers import ComplexAvgPooling2D as AveragePooling2D
    from cvnn.layers import ComplexFlatten as Flatten
    from cvnn.layers import ComplexInput as Input
    from cvnn.layers import ComplexDropout as Dropout


def get_model(verbose: bool = False):
    print(f"Using {config['model']} model")
    if config['model'] == 'chen':
        model, input_shape = get_chen_model()
    elif config['model'] == 'ding':
        model, input_shape = get_ding_model()
    elif config['model'] == 'own':
        model, input_shape = get_own_model()
    elif config['model'] == 'mlp':
        model, input_shape = get_mlp_model()
    elif config['model'] == 'polsar':
        model, input_shape = get_polsar_model()
    else:
        raise ValueError(f"Unknown requested model {config['model']}")
    if verbose:
        model.summary()
    return model, input_shape


def get_polsar_model():
    model = tf.keras.models.Sequential()
    if config['tensorflow']:
        model.add(Input(shape=(128, 128, 1)))  # Always use ComplexInput at the start
    else:
        model.add(Input(input_shape=(128, 128, 1)))  # Always use ComplexInput at the start
    model.add(Conv2D(6, (3, 3), activation='cart_relu'))
    model.add(AveragePooling2D((2, 2)))
    model.add(Conv2D(12, (3, 3), activation='cart_relu'))
    model.add(Flatten())
    model.add(Dense(108, activation='cart_relu'))
    model.add(Dense(10, activation='softmax_real'))
    model.compile(optimizer='adam',
                  loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                  metrics=['accuracy'])
    return model, (128, 128)


def get_mlp_model():
    input_shape = (128, 128)
    assert config['model'] == 'mlp'
    model = tf.keras.models.Sequential()
    if config['tensorflow']:
        model.add(Input(shape=input_shape + (1,)))  # Always use ComplexInput at the start
    else:
        model.add(Input(input_shape=input_shape + (1,), dtype=config['dtype']))  # Always use ComplexInput at the start
    model.add(Flatten(dtype=config['dtype']))
    model.add(Dense(512, activation='cart_relu', dtype=config['dtype']))
    model.add(Dropout(0.5, dtype=config['dtype']))
    model.add(Dense(128, activation='cart_relu', dtype=config['dtype']))
    model.add(Dropout(0.5, dtype=config['dtype']))
    model.add(Dense(10, activation='softmax_real', dtype=config['dtype']))
    model.compile(optimizer='adam',
                  loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                  metrics=['accuracy'])
    return model, input_shape


def get_own_model():
    assert config['model'] == 'own'
    input_shape = (128, 128)
    model = tf.keras.models.Sequential()
    if config['tensorflow']:
        model.add(Input(shape=input_shape + (1,)))  # Always use ComplexInput at the start
    else:
        model.add(Input(input_shape=input_shape + (1,), dtype=config['dtype']))  # Always use ComplexInput at the start
    model.add(Conv2D(64, (3, 3), activation='cart_relu', dtype=config['dtype']))
    model.add(AveragePooling2D((2, 2), dtype=config['dtype']))
    model.add(Conv2D(32, (3, 3), activation='cart_relu', dtype=config['dtype']))
    model.add(AveragePooling2D((2, 2), dtype=config['dtype']))
    model.add(Flatten(dtype=config['dtype']))
    model.add(Dense(128, activation='cart_relu', dtype=config['dtype']))
    model.add(Dropout(0.5, dtype=config['dtype']))
    model.add(Dense(10, activation='softmax_real', dtype=config['dtype']))
    model.compile(optimizer='adam',
                  loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                  metrics=['accuracy'])
    return model, input_shape


def get_ding_model():
    # TODO: log-loss
    # TODO: Could not find sgd params
    assert config['model'] == 'ding'
    input_shape = (128, 128)
    model = tf.keras.models.Sequential()
    if config['tensorflow']:
        model.add(Input(shape=input_shape + (1,)))  # Always use ComplexInput at the start
    else:
        model.add(Input(input_shape=input_shape + (1,), dtype=config['dtype']))  # Always use ComplexInput at the start

    model.add(Conv2D(96, (3, 3), activation='cart_relu', dtype=config['dtype']))
    model.add(Conv2D(96, (3, 3), activation='cart_relu', dtype=config['dtype']))

    model.add(MaxPooling2D((2, 2), strides=1, dtype=config['dtype']))

    model.add(Conv2D(256, (3, 3), activation='cart_relu', dtype=config['dtype']))
    model.add(MaxPooling2D((2, 2), strides=1, dtype=config['dtype']))

    model.add(Flatten(dtype=config['dtype']))
    model.add(Dense(10, activation='softmax_real', dtype=config['dtype']))

    model.compile(optimizer='SGD',
                  loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                  metrics=['accuracy'])
    return model, input_shape


def get_chen_model():
    # TODO: I still have to implement the weight decay. Options:
    #   USing addon: https://www.tensorflow.org/addons/api_docs/python/tfa/optimizers/SGDW
    #   Add L2-reg
    # TODO: Change learning rate after 50 epochs
    # TODO: Check Loss
    assert config['model'] == 'chen'
    input_shape = (88, 88)
    model = tf.keras.models.Sequential()
    if config['tensorflow']:
        model.add(Input(shape=input_shape + (1,)))  # Always use ComplexInput at the start
    else:
        model.add(Input(input_shape=input_shape + (1,), dtype=config['dtype']))  # Always use ComplexInput at the start

    model.add(Conv2D(16, (5, 5), activation='cart_relu', dtype=config['dtype']))
    model.add(MaxPooling2D((2, 2), strides=2, dtype=config['dtype']))

    model.add(Conv2D(32, (5, 5), activation='cart_relu', dtype=config['dtype']))
    model.add(MaxPooling2D((2, 2), strides=2, dtype=config['dtype']))

    model.add(Conv2D(64, (6, 6), activation='cart_relu', dtype=config['dtype']))
    model.add(MaxPooling2D((2, 2), strides=2, dtype=config['dtype']))

    model.add(Dropout(0.5, dtype=config['dtype']))
    model.add(Conv2D(128, (5, 5), activation='cart_relu', dtype=config['dtype']))

    model.add(Conv2D(10, (3, 3), activation='softmax_real', dtype=config['dtype']))

    model.compile(optimizer=tf.keras.optimizers.SGD(learning_rate=0.001, momentum=0.9, name='SGD'),
                  loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                  metrics=['accuracy'])
    return model, input_shape


def get_data(input_shape):
    img_train, img_test, labels_train, labels_test = get_train_and_test()
    img_train = np.array([resize_image(img, input_shape=input_shape) for img in img_train])
    img_test = np.array([resize_image(img, input_shape=input_shape) for img in img_test])
    img_train = np.array(img_train.reshape(img_train.shape + (1,)))
    img_test = np.array(img_test.reshape(img_test.shape + (1,)))
    if config['dtype'] == np.float32:
        img_train == np.abs(img_train)
        img_test == np.abs(img_test)
    return img_train, img_test, labels_train, labels_test


def save_results(model, history):
    path = create_folder('./log/')
    pd.DataFrame.from_dict(history.history).to_csv(path / 'history.csv', index=False)
    if saver_config['hist_plot']:
        plot_history(history, path / 'accuracy.png', False)
    if saver_config['model_summary']:
        with open(path / 'model_summary.txt', 'w') as fh:
            model.summary(print_fn=lambda x: fh.write(x + '\n'))
    if saver_config['add_to_excel']:
        fieldsname = []
        values = []
        for key, value in config.items():
            fieldsname.append(key)
            values.append(str(value))
        for key, value in history.history.items():
            fieldsname.append(key)
            values.append(str(value[-1]))
        fieldsname.append('path')
        values.append(str(path))
        create_excel_file(fieldsname, values, percentage_cols=[])
    if saver_config['json']:
        json_dict = {
            'name': model.name,
            'loss': tf.keras.losses.serialize(model.loss),
            'optimizer': tf.keras.optimizers.serialize(model.optimizer),
            'layers': [tf.keras.layers.serialize(layer) for layer in model.layers]
        }
        with open(path / 'model_arch.pkl', 'w') as fp:
            pickle.dump(json_dict, fp, protocol=pickle.HIGHEST_PROTOCOL)


if __name__ == '__main__':
    if config['dtype'] == np.complex64 and config['tensorflow']:
        raise ValueError("Tensorflow mode does not support complex dtype")
    # Get model
    model, input_shape = get_model(True)
    # Get data
    img_train, img_test, labels_train, labels_test = get_data(input_shape=input_shape)
    # Train
    history = model.fit(x=img_train, y=labels_train,
                        validation_data=(img_test, labels_test),
                        epochs=config['epochs'], batch_size=config['batch_size'])
    # Save results
    save_results(model=model, history=history)
