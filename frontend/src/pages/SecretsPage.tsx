import { useState, useEffect, useCallback } from 'react';
import type { SecretMetadata, PaginatedResponse } from '../types';
import { secretsApi } from '../api';
import { useAuth } from '../contexts';
import { SecretModal, ConfirmModal } from '../components';

export function SecretsPage() {
  const { user, logout } = useAuth();
  const [secrets, setSecrets] = useState<SecretMetadata[]>([]);
  const [pagination, setPagination] = useState({ page: 1, pages: 1, total: 0 });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingSecretId, setEditingSecretId] = useState<string | null>(null);
  const [viewingSecretId, setViewingSecretId] = useState<string | null>(null);
  const [deletingSecretId, setDeletingSecretId] = useState<string | null>(null);

  const loadSecrets = useCallback(async (page = 1) => {
    setIsLoading(true);
    setError('');
    try {
      const response: PaginatedResponse<SecretMetadata> = await secretsApi.list(page);
      setSecrets(response.items);
      setPagination({ page: response.page, pages: response.pages, total: response.total });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load secrets');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSecrets();
  }, [loadSecrets]);

  const handleDelete = async () => {
    if (!deletingSecretId) return;
    try {
      await secretsApi.delete(deletingSecretId);
      setDeletingSecretId(null);
      loadSecrets(pagination.page);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete secret');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="secrets-page">
      <header className="secrets-header">
        <div className="header-left">
          <h1>🔐 SecureVault</h1>
          <span className="user-email">{user?.email}</span>
        </div>
        <div className="header-right">
          <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
            + New Secret
          </button>
          <button className="btn btn-secondary" onClick={logout}>
            Logout
          </button>
        </div>
      </header>

      <main className="secrets-main">
        {error && <div className="error-message">{error}</div>}

        {isLoading ? (
          <div className="loading">Loading your secrets...</div>
        ) : secrets.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🔒</div>
            <h2>No secrets yet</h2>
            <p>Create your first secret to get started</p>
            <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
              Create Secret
            </button>
          </div>
        ) : (
          <>
            <div className="secrets-list">
              {secrets.map((secret) => (
                <div key={secret.id} className="secret-card">
                  <div className="secret-info">
                    <h3>{secret.name}</h3>
                    <p className="secret-date">Created {formatDate(secret.created_at)}</p>
                  </div>
                  <div className="secret-actions">
                    <button
                      className="btn btn-icon"
                      onClick={() => setViewingSecretId(secret.id)}
                      title="View"
                    >
                      👁
                    </button>
                    <button
                      className="btn btn-icon"
                      onClick={() => setEditingSecretId(secret.id)}
                      title="Edit"
                    >
                      ✏️
                    </button>
                    <button
                      className="btn btn-icon btn-danger"
                      onClick={() => setDeletingSecretId(secret.id)}
                      title="Delete"
                    >
                      🗑
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {pagination.pages > 1 && (
              <div className="pagination">
                <button
                  className="btn btn-secondary"
                  disabled={pagination.page <= 1}
                  onClick={() => loadSecrets(pagination.page - 1)}
                >
                  Previous
                </button>
                <span>
                  Page {pagination.page} of {pagination.pages}
                </span>
                <button
                  className="btn btn-secondary"
                  disabled={pagination.page >= pagination.pages}
                  onClick={() => loadSecrets(pagination.page + 1)}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </main>

      {/* Create Modal */}
      {showCreateModal && (
        <SecretModal
          mode="create"
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            loadSecrets(pagination.page);
          }}
        />
      )}

      {/* View Modal */}
      {viewingSecretId && (
        <SecretModal
          mode="view"
          secretId={viewingSecretId}
          onClose={() => setViewingSecretId(null)}
        />
      )}

      {/* Edit Modal */}
      {editingSecretId && (
        <SecretModal
          mode="edit"
          secretId={editingSecretId}
          onClose={() => setEditingSecretId(null)}
          onSuccess={() => {
            setEditingSecretId(null);
            loadSecrets(pagination.page);
          }}
        />
      )}

      {/* Delete Confirmation */}
      {deletingSecretId && (
        <ConfirmModal
          title="Delete Secret"
          message="Are you sure you want to delete this secret? This action cannot be undone."
          confirmText="Delete"
          onConfirm={handleDelete}
          onCancel={() => setDeletingSecretId(null)}
        />
      )}
    </div>
  );
}
