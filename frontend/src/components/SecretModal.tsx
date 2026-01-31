import { useState, useEffect, type FormEvent } from 'react';
import type { Secret } from '../types';
import { secretsApi } from '../api';

interface SecretModalProps {
  mode: 'create' | 'view' | 'edit';
  secretId?: string;
  onClose: () => void;
  onSuccess?: () => void;
}

export function SecretModal({ mode, secretId, onClose, onSuccess }: SecretModalProps) {
  const [name, setName] = useState('');
  const [content, setContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showContent, setShowContent] = useState(mode === 'create');

  // Load secret data for view/edit modes
  useEffect(() => {
    if ((mode === 'view' || mode === 'edit') && secretId) {
      setIsLoading(true);
      secretsApi
        .get(secretId)
        .then((secret: Secret) => {
          setName(secret.name);
          setContent(secret.content);
        })
        .catch((err) => {
          setError(err instanceof Error ? err.message : 'Failed to load secret');
        })
        .finally(() => {
          setIsLoading(false);
        });
    }
  }, [mode, secretId]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (mode === 'create') {
        await secretsApi.create({ name, content });
      } else if (mode === 'edit' && secretId) {
        await secretsApi.update(secretId, { name, content });
      }
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Operation failed');
    } finally {
      setIsLoading(false);
    }
  };

  const title = {
    create: 'Create New Secret',
    view: 'View Secret',
    edit: 'Edit Secret',
  }[mode];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{title}</h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}

        {isLoading && mode !== 'create' ? (
          <div className="modal-loading">Loading...</div>
        ) : mode === 'view' ? (
          <div className="modal-content">
            <div className="form-group">
              <label>Name</label>
              <p className="view-value">{name}</p>
            </div>
            <div className="form-group">
              <label>
                Content
                <button
                  type="button"
                  className="toggle-visibility"
                  onClick={() => setShowContent(!showContent)}
                >
                  {showContent ? '🙈 Hide' : '👁 Show'}
                </button>
              </label>
              <pre className={`view-content ${!showContent ? 'masked' : ''}`}>
                {showContent ? content : '••••••••••••••••'}
              </pre>
            </div>
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={onClose}>
                Close
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="modal-content">
            <div className="form-group">
              <label htmlFor="secret-name">Name</label>
              <input
                id="secret-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="My API Key"
                required
                autoFocus
              />
            </div>

            <div className="form-group">
              <label htmlFor="secret-content">
                Secret Content
                <button
                  type="button"
                  className="toggle-visibility"
                  onClick={() => setShowContent(!showContent)}
                >
                  {showContent ? '🙈 Hide' : '👁 Show'}
                </button>
              </label>
              <textarea
                id="secret-content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Enter your secret value..."
                rows={5}
                required
                className={!showContent ? 'masked' : ''}
              />
            </div>

            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={isLoading}>
                {isLoading ? 'Saving...' : mode === 'create' ? 'Create' : 'Save Changes'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
