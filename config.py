class Config:
    STATE_SIZE = 5
    ACTION_SIZE = 4
    MAX_STEPS = 50
    SEED = 42

    # Training episode settings
    EPISODES = 10_000
    LOG_EVERY = 2_000
    CHECKPOINT_EVERY = 5_000

    # DQN hyperparameters
    DQN_ALPHA = 0.001
    DQN_GAMMA = 0.95
    DQN_EPSILON = 1.0
    DQN_EPSILON_MIN = 0.10  # raised from 0.01 — prevents premature policy lock
    DQN_EPSILON_DECAY = 0.9995
    DQN_BATCH_SIZE = 64
    DQN_TARGET_UPDATE = 100
    DQN_BUFFER_CAP = 20_000

    # Q-Learning hyperparameters (referenced by train_now.py)
    QL_ALPHA = 0.10
    QL_GAMMA = 0.95
    QL_EPSILON = 1.0
    QL_EPSILON_MIN = 0.01
    QL_EPSILON_DECAY = 0.995

    MODEL_DIR = "models"
    DQN_MODEL_PATH = "models/dqn.pkl"
    DQN_WEIGHTS_PATH = "models/dqn_weights.pt"

    FLASK_HOST = "127.0.0.1"
    FLASK_PORT = 5000
    FLASK_DEBUG = False
