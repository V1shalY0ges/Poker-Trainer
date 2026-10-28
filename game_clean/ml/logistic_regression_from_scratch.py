import numpy as np  # Import numpy for numerical operations and array handling

class LogisticRegressionSGD:
    def __init__(self, lr=0.05, n_iter=1000, n_classes=3, batch_size=32, tol=1e-4, verbose=False):
        """
        A vectorised, mini-batch Stochastic Gradient Descent (SGD) Logistic Regression
        implemented from scratch.
        Supports multi-class classification (softmax) suitable for poker actions:
        fold, call, raise.
        """
        self.lr = lr  # Learning rate for gradient descent
        self.n_iter = n_iter  # Maximum number of epochs for training
        self.n_classes = n_classes  # Number of classes (poker actions)
        self.batch_size = batch_size  # Mini-batch size for SGD
        self.tol = tol  # Tolerance for early stopping based on loss change
        self.verbose = verbose  # Whether to print training progress
        self.weights = None  # Weights of the model (to be initialised in fit)
        self.bias = None  # Bias terms of the model (to be initialised in fit)

    def _softmax(self, z):
        """
        Softmax function converts raw scores into probabilities for multi-class classification.
        """
        # Subtract max for numerical stability to avoid large exponentials
        exp_z = np.exp(z - np.max(z, axis=1, keepdims=True))
        # Divide by sum along classes to get probabilities
        return exp_z / np.sum(exp_z, axis=1, keepdims=True)

    def _one_hot(self, y):
        """
        Converts integer labels into one-hot encoded vectors.
        e.g., 0 → [1,0,0], 1 → [0,1,0], 2 → [0,0,1]
        """
        n_samples = y.shape[0]  # Number of samples
        y_onehot = np.zeros((n_samples, self.n_classes))  # Initialise all zeros
        y_onehot[np.arange(n_samples), y] = 1  # Set correct class to 1
        return y_onehot

    def fit(self, X, y):
        """
        Train the logistic regression model using mini-batch SGD.
        X : ndarray, shape (n_samples, n_features)
            Feature matrix
        y : ndarray, shape (n_samples,)
            Integer class labels
        """
        n_samples, n_features = X.shape  # Extract dimensions of data

        # Initialise weights and bias to zeros
        self.weights = np.zeros((n_features, self.n_classes))
        self.bias = np.zeros(self.n_classes)

        # Convert labels to one-hot encoding
        y_onehot = self._one_hot(y)

        prev_loss = np.inf  # Keep track of previous loss for early stopping

        # Loop through each epoch
        for epoch in range(self.n_iter):
            # Shuffle data to randomise mini-batches each epoch
            indices = np.random.permutation(n_samples)
            X_shuffled = X[indices]
            y_shuffled = y_onehot[indices]

            # Process mini-batches
            for start in range(0, n_samples, self.batch_size):
                end = start + self.batch_size
                X_batch = X_shuffled[start:end]  # Select batch features
                y_batch = y_shuffled[start:end]  # Select batch labels

                # Forward pass: compute raw scores
                z = X_batch @ self.weights + self.bias  # Matrix multiplication + bias
                probs = self._softmax(z)  # Convert scores to probabilities

                # Compute gradient of loss w.r.t weights and bias
                error = probs - y_batch  # Difference between predicted and true
                grad_w = X_batch.T @ error / X_batch.shape[0]  # Gradient for weights
                grad_b = np.mean(error, axis=0)  # Gradient for bias

                # Update weights and bias using gradient descent
                self.weights -= self.lr * grad_w
                self.bias -= self.lr * grad_b

            # Compute loss over entire dataset for monitoring
            z_all = X @ self.weights + self.bias
            probs_all = self._softmax(z_all)
            # Cross-entropy loss with small epsilon to prevent log(0)
            loss = -np.mean(np.sum(y_onehot * np.log(probs_all + 1e-15), axis=1))

            # Print progress every 50 epochs if verbose
            if self.verbose and epoch % 50 == 0:
                print(f"Epoch {epoch} - Loss: {loss:.5f}")

            # Early stopping if loss change is below tolerance
            if abs(prev_loss - loss) < self.tol:
                if self.verbose:
                    print(f"[SGD] Early stopping at epoch {epoch} - Loss change < tol")
                break
            prev_loss = loss  # Update previous loss

    def predict_proba(self, X):
        """
        Predict class probabilities for input features X.
        Returns array of shape (n_samples, n_classes)
        """
        z = X @ self.weights + self.bias  # Compute raw scores
        return self._softmax(z)  # Convert to probabilities

    def predict(self, X):
        """
        Predict the most likely class for input features X.
        Returns array of shape (n_samples,)
        """
        probs = self.predict_proba(X)  # Get probabilities
        return np.argmax(probs, axis=1)  # Return index of max probability (class label)
