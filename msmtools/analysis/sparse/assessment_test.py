"""This module provides unit tests for the assessment module"""
from __future__ import absolute_import
from __future__ import division
import unittest

import numpy as np
# from numpy.core.numeric import ndarray

import scipy.sparse
from scipy.sparse.dia import dia_matrix

from . import assessment
from six.moves import range


def normalize_rows(A):
    """Normalize rows of sparse marix"""
    A = A.tocsr()
    values = A.data
    indptr = A.indptr  # Row index pointers
    indices = A.indices  # Column indices

    dim = A.shape[0]
    normed_values = np.zeros(len(values))

    for i in range(dim):
        thisrow = values[indptr[i]:indptr[i + 1]]
        rowsum = np.sum(thisrow)
        normed_values[indptr[i]:indptr[i + 1]] = thisrow / rowsum

    return scipy.sparse.csr_matrix((normed_values, indices, indptr))


def random_nonempty_rows(M, N, density=0.01):
    """Generate a random sparse matrix with nonempty rows"""
    N_el = int(density * M * N)  # total number of non-zero elements
    if N_el < M:
        raise ValueError("Density too small to obtain nonempty rows")
    else:
        rows = np.zeros(N_el)
        rows[0:M] = np.arange(M)
        rows[M:N_el] = np.random.random_integers(0, M - 1, size=(N_el - M,))
        cols = np.random.random_integers(0, N - 1, size=(N_el,))
        values = np.random.rand(N_el)
        return scipy.sparse.coo_matrix((values, (rows, cols)))


class TestTransitionMatrix(unittest.TestCase):
    def setUp(self):
        self.dim = 10000
        self.density = 0.001
        self.tol = 1e-15
        A = random_nonempty_rows(self.dim, self.dim, density=self.density)
        self.T = normalize_rows(A)

    def tearDown(self):
        pass

    def test_is_transition_matrix(self):
        self.assertTrue(assessment.is_transition_matrix(self.T, tol=self.tol))


class TestRateMatrix(unittest.TestCase):
    def create_sparse_rate_matrix(self):
        """
        constructs the following rate matrix for a M/M/1 queue
        TODO: fix math string
        :math: `
        Q = \begin{pmatrix}
        -\lambda & \lambda \\
        \mu & -(\mu+\lambda) & \lambda \\
        &\mu & -(\mu+\lambda) & \lambda \\
        &&\mu & -(\mu+\lambda) & \lambda &\\
        &&&&\ddots
        \end{pmatrix}`
        taken from: https://en.wikipedia.org/wiki/Transition_rate_matrix
        """
        lambda_ = 5
        mu = 3
        dim = self.dim

        diag = np.empty((3, dim))
        # main diagonal
        diag[0, 0] = (-lambda_)
        diag[0, 1:dim - 1] = -(mu + lambda_)
        diag[0, dim - 1] = lambda_

        # lower diag
        diag[1, :] = mu
        diag[1, -2:] = -mu
        diag[1, -2:] = lambda_
        diag[0, dim - 1] = -lambda_
        # upper diag
        diag[2, :] = lambda_

        offsets = [0, -1, 1]

        return dia_matrix((diag, offsets), shape=(dim, dim))

    def setUp(self):
        self.dim = 10
        self.K = self.create_sparse_rate_matrix()
        self.tol = 1e-15

    def test_is_rate_matrix(self):
        K_copy = self.K.copy()
        self.assertTrue(assessment.is_rate_matrix(self.K, self.tol), "K should be evaluated as rate matrix.")

        self.assertTrue(np.allclose(self.K.data, K_copy.data) and \
                        np.allclose(self.K.offsets, K_copy.offsets), "object modified!")


class TestReversible(unittest.TestCase):
    def create_rev_t(self):
        dim = self.dim

        diag = np.zeros((3, dim))

        # forward_p = 4 / 5.
        forward_p = 0.6
        backward_p = 1 - forward_p
        # main diagonal
        diag[0, 0] = backward_p
        diag[0, -1] = backward_p

        # lower diag
        diag[1, :] = backward_p
        diag[1, 1] = forward_p

        # upper diag
        diag[2, :] = forward_p

        return dia_matrix((diag, [0, 1, -1]), shape=(dim, dim))

    def setUp(self):
        self.dim = 100
        self.tol = 1e-15
        self.T = self.create_rev_t()

    def test_is_reversible(self):
        self.assertTrue(assessment.is_reversible(self.T, tol=self.tol), \
                        'matrix should be reversible')


class TestIsConnected(unittest.TestCase):
    def setUp(self):
        C1 = 1.0 * np.array([[1, 4, 3], [3, 2, 4], [4, 5, 1]])
        C2 = 1.0 * np.array([[0, 1], [1, 0]])
        C3 = 1.0 * np.array([[7]])

        C = scipy.sparse.block_diag((C1, C2, C3))

        C = C.toarray()
        """Forward transition block 1 -> block 2"""
        C[2, 3] = 1
        """Forward transition block 2 -> block 3"""
        C[4, 5] = 1

        self.T_connected = scipy.sparse.csr_matrix(C1 / C1.sum(axis=1)[:, np.newaxis])
        self.T_not_connected = scipy.sparse.csr_matrix(C / C.sum(axis=1)[:, np.newaxis])

    def tearDown(self):
        pass

    def test_connected_count_matrix(self):
        """Directed"""
        is_connected = assessment.is_connected(self.T_not_connected)
        self.assertFalse(is_connected)

        is_connected = assessment.is_connected(self.T_connected)
        self.assertTrue(is_connected)

        """Undirected"""
        is_connected = assessment.is_connected(self.T_not_connected, directed=False)
        self.assertTrue(is_connected)


if __name__ == "__main__":
    import cProfile as profiler

    unittest.main()
    profiler.run('unittest.main()', sort=1)