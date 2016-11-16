from Stemmer import Stemmer
from collections import Counter, UserString
from math import log, sqrt

import numpy as np
import scipy
import stop_words
from faker import Factory
from lazyutils import lazy
from scipy.cluster.vq import whiten

fake = Factory.create(locale='pt-br')
stemmer = Stemmer('portuguese')
DEFAULT_STOP_WORDS = stop_words.get_stop_words('portuguese')


def fake_text(paragraphs=None):
    """
    Create a string of fake text with several paragraphs.

    Args:
        paragraphs (int):
            Optional number of paragraphs.
    """

    if paragraphs is None:
        data = fake.paragraphs()
    else:
        data = fake.paragraphs(nb=paragraphs)
    return '\n\n'.join(data)


def strip_punctuation(word):
    """
    Remove punctuation from the end of word.
    """

    return word.rstrip('.,:;?!')


def stemize(text, stop_words=None):
    """
    Receive a string of text and return a list of stems.
    """

    if stop_words is None:
        stop_words = DEFAULT_STOP_WORDS
    stop_stems = set(stemmer.stemWords(stop_words))
    words = text.casefold().split()
    words = stemmer.stemWords([strip_punctuation(word) for word in words])
    return [w for w in words if w not in stop_stems]


def _force_stemize(data):
    """
    Internal function: return argument if it is a list of stems or return
    stemize(data) if it is a string.
    """

    if isinstance(data, str):
        return stemize(data)
    else:
        return list(data)


def bag_of_words(data, method='boolean', weights=None):
    """
    Convert a text to a Counter object.

    Args:
        data:
            Can be a string of text or a list of stems. If data is a string, it
            will be converted to a list of stems using the stemize() function.
        method:
            Weighting factor used in as the values of the Counter object.

            'boolean' (default):
                Existing words receive a value of 1.
            'frequency':
                Weight corresponds to the relative frequency of each words
            'count':
                Weight corresponds to the number of times the word appears on
                text.
            'weighted':
                Inverse frequency weighting method.
        weights:
            ??
    """

    data = _force_stemize(data)
    count = Counter(data)

    if method == 'boolean':
        return Counter({stem: 1 for stem in count})
    elif method == 'frequency':
        total = sum(count.values())
        return Counter({stem: n / total for (stem, n) in count.items()})
    elif method == 'count':
        return count
    elif method == 'weighted':
        counter = bag_of_words(data, 'frequency')
        return Counter({stem: weights.get(stem, 1) * freq
                        for (stem, freq) in counter.items()})
    else:
        raise ValueError('invalid method: %r' % method)


def cos_angle(u, v):
    """
    Return the cosine of the angle between two vectors.
    """

    return u.dot(v) / (norm(u) * norm(v))


def norm(u):
    """
    Euclidean norm of vector u.
    """

    return sqrt((u * u).sum())


def similarity(u, v, method='triangular'):
    """
     Return a normalized measure of similarity between two vectors.

    The resulting value is between 0 (no similarity) and 1 (identity).
    """

    if method == 'angle':
        return (cos_angle(u, v) + 1) / 2
    elif method == 'triangular':
        return 1 - norm(u - v) / (norm(u) + norm(v))
    else:
        raise ValueError('invalid similarity method: %r' % method)


class Text(UserString):
    """
    Represents a text with metadata from NLP.
    """

    @lazy
    def bow_boolean(self):
        return bag_of_words(self.stems, 'boolean')

    @lazy
    def bow_frequency(self):
        return bag_of_words(self.stems, 'frequency')

    @lazy
    def bow_count(self):
        return bag_of_words(self.stems, 'count')

    @lazy
    def bow_weighted(self):
        if self.weights is None:
            raise AttributeError('must define .weights attribute before')
        return bag_of_words(self.stems, 'weighted', weights=self.weights)

    @lazy
    def bow(self):
        return self.bag_of_words(self.method)

    def __init__(self, data, method=None, stop_words=stop_words):
        super().__init__(data)
        self.stems = stemize(data, stop_words=stop_words)
        self.weights = None
        self.method = None

    def __repr__(self):
        data = self.data
        if len(data) >= 10:
            data = data[:10] + '...'
        return '%s(%r)' % (type(self).__name__, data)

    def __str__(self):
        return self.data

    def words(self):
        """
        Return a sorted list of unique words or stems present in text.
        """

        return sorted(set(self.stems))

    def bag_of_words(self, method=None):
        """
        Return a Counter object from computing a bag of words using the given
        method.

        Args:
            method (str):
                Same meaning as the ``method`` attribute in the :func:`bag_of_words`
                function.
        """

        if method is None:
            if self.method is None:
                raise RuntimeError('must define the default method')
            return self.bow

        if method == 'weighted' and self.weights is None:
            raise RuntimeError('must define the .weights attribute first')
        try:
            return getattr(self, 'bow_' + method)
        except AttributeError:
            raise ValueError('invalid method: %r' % method)


class NLPJob:
    """
    Represent a natural language processing job.

    Parameters:
        texts: list of text strings
    """

    @property
    def method(self):
        return self._method

    @method.setter
    def method(self, value):
        self._update_method(value)

    def __init__(self, texts=(), method='weighted', stop_words=None):
        self._texts = [Text(data, stop_words=stop_words) for data in texts]
        self._method = method
        self._update_method(method)
        self._update_weights()

    def __len__(self):
        return len(self._texts)

    def __iter__(self):
        for text in self._texts:
            yield text.data

    def __getitem__(self, idx):
        return self._texts[idx].data

    def words(self):
        """
        Return a list of words from all texts.
        """

        words = set()
        for text in self._texts:
            words.update(text.words())
        return sorted(words)

    def common_words(self, n=None, by_document=False):
        """
        Return a list of (word, frequency) pairs for the the n-th most common
        words.
        """

        counter = Counter()
        if by_document:
            N = len(self._texts)
            for text in self._texts:
                counter += text.bow_boolean
            common = counter.most_common(n)
            return [(word, n / N) for (word, n) in common]
        else:
            for text in self._texts:
                counter += text.bow_count
            total = sum(counter.values())
            common = counter.most_common(n)
            return [(word, count / total) for (word, count) in common]

    def document_frequency(self):
        """
        Return a Counter mapping counting the number of texts in which each word
        appears.
        """

        counter = Counter()
        for text in self._texts:
            counter += Counter(text.bow_boolean)
        return counter

    def weights(self):
        """
        Compute weights for each word based on the logarithm of the total number
        of documents over the document frequency.
        """

        N = len(self._texts)
        frequencies = self.document_frequency()
        weights = {stem: log(N / freq) for (stem, freq) in frequencies.items()}
        return weights

    def _update_weights(self):
        """
        Update the weights factor for all texts in the NPLJob.
        """

        weights = self.weights()
        for text in self._texts:
            text.weights = weights

    def _update_method(self, method):
        """
        Update default method.
        """

        for text in self._texts:
            text.method = method
        self._method = method

    def vector(self, i):
        """
        Return the i-th document as a :class:`numpy.array`. Each component
        corresponds to the value in the counter object. Components are ordered
        as the list returned by self.words()
        """

        text = self._texts[i]
        words = self.words()
        return np.array([text.bow.get(w, 0.0) for w in words])

    def matrix(self):
        """
        Convert documents to a matrix
        """

        N = len(self._texts)
        return np.array([self.vector(i) for i in range(N)])

    def _cos_angle(self, i, j):
        """
        Same as cos(self.angle(i, j))
        """

        u = self.vector(i)
        v = self.vector(j)
        return cos_angle(u, v)

    def angle(self, i, j):
        """
        Angle between vectors created from the i-th and j-th texts in Euclidean
        space (in radians).
        """

        return np.arccos(self._cos_angle(i, j))

    def similarity(self, i, j, method='triangular'):
        """
        Return a normalized measure of similarity between the i-th and j-th
        texts. The resulting value is between 0 (no similarity) and 1
        (identity).

        Args:
            i, j (int):
                Index for the respective text.
            method:
                One of 'angle',
        """

        return similarity(self.vector(i), self.vector(j), method=method)

    def similarity_matrix(self, method='triangular'):
        """
        Return the similarity matrix for all pairs of i, j.
        """

        N = len(self._texts)
        similarity = np.ones([N, N], dtype=float)
        for i in range(N):
            for j in range(i + 1, N):
                value = self.similarity(i, j, method)
                similarity[i, j] = similarity[j, i] = value
        return similarity


def kmeans(job, k, whiten=True):
    """
    Performs a k-means classification for all documents in the given job.

    Args:
        job (list or NPLJob):
            A list of texts or a natural language processing job (NPLJob)
            instance.
        k (int):
            The desired number of clusters.

    Return:
        centroids:
            A 2D array with all found centroids.
        labels:
            A sequence in witch the i-th element correspond to the cluster index
            for the i-th document.
    """

    if not isinstance(job, NLPJob):
        job = NLPJob(job)

    data = job.matrix()
    std = 1
    if whiten:
        std = data.std(axis=0)
        std[std == 0] = 1
        data /= std[None, :]
    centroids, labels = scipy.cluster.vq.kmeans2(data, k, minit='points')
    centroids *= std
    return centroids, labels


data = [fake_text(10) for _ in range(10)]
job = NLPJob(data)
print(job.document_frequency())
print(job.similarity_matrix())
print()

s = job.similarity_matrix()
print(s.max(), s.min())

centroids, labels = kmeans(job, 3)
a, b, c = centroids
print(similarity(a, b))
print(similarity(a, c))
print(similarity(b, c))
print(job.common_words(20, by_document=True))
