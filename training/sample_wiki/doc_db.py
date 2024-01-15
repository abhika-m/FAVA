#!/usr/bin/env python3
# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
"""Documents, in a sqlite database."""

import sqlite3
import unicodedata


def normalize(text):
    """Resolve different type of unicode encodings."""
    return unicodedata.normalize('NFD', text)


class DocDB(object):
    """Sqlite backed document storage.

    Implements get_doc_text(doc_id).
    """

    def __init__(self, db_path=None):
        self.path = db_path
        self.connection = sqlite3.connect(self.path, check_same_thread=False)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def path(self):
        """Return the path to the file that backs this database."""
        return self.path

    def close(self):
        """Close the connection to the database."""
        self.connection.close()

    def get_doc_title(self):
        """Fetch all ids of docs stored in the db."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT title FROM documents")
        results = [r[0] for r in cursor.fetchall()]
        cursor.close()
        return results

    def get_doc_text(self, doc_id, normalize=False):
        """Fetch the raw text of the doc for 'doc_id'."""
        cursor = self.connection.cursor()
        if normalize is True:
            cursor.execute(
                "SELECT text FROM documents WHERE title = ?",
                (normalize(doc_id),)
            )
        else:
            cursor.execute(
                "SELECT text FROM documents WHERE title = ?",
                (doc_id,)
            )
        result = cursor.fetchone()
        cursor.close()
        return result if result is None else result[0]
    
    def get_doc_id(self, doc_id, normalize=False):
        """Fetch the raw text of the doc for 'doc_id'."""
        cursor = self.connection.cursor()
        if normalize is True:
            cursor.execute(
                "SELECT id FROM documents WHERE title = ?",
                (normalize(doc_id),)
            )
        else:
            cursor.execute(
                "SELECT id FROM documents WHERE title = ?",
                (doc_id,)
            )
        result = cursor.fetchone()
        cursor.close()
        return result if result is None else result[0]
    
    def get_doc_title_longer_than_n(self, n):
        """
        Fetch ids of docs whose text length is longer than n characters.
        If we set longer than 
        - 100k characters --> 1437 articles
        - 10k characters --> 329886 articles
        - 1k characters --> 3361196 articles
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT title FROM documents where length > ?", (n,))
        results = [r[0] for r in cursor.fetchall()]
        cursor.close()
        return results
