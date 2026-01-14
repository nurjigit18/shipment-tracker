import { useEffect, useState } from 'react';
import { apiClient } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { Users as UsersIcon, Loader2, AlertCircle, Plus, X, Trash2, UserX, CheckCircle2 } from 'lucide-react';

interface User {
  id: number;
  username: string;
  role: string;
  organization_name: string;
  fulfillment_name?: string | null;
}

interface Organization {
  id: number;
  name: string;
}

interface Role {
  id: number;
  name: string;
}

interface Fulfillment {
  id: number;
  name: string;
}

export function Users() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [fulfillments, setFulfillments] = useState<Fulfillment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [userToDelete, setUserToDelete] = useState<User | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [showAddExistingForm, setShowAddExistingForm] = useState(false);
  const [searchUsername, setSearchUsername] = useState('');
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [searching, setSearching] = useState(false);
  const [addingUser, setAddingUser] = useState(false);
  const [addError, setAddError] = useState('');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    role_name: '',
    organization_id: 0,
    fulfillment_id: 0
  });

  useEffect(() => {
    loadUsers();
    loadOrganizations();
    loadRoles();
    loadFulfillments();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await apiClient.get<User[]>('/api/users');
      setUsers(data);
    } catch (e: any) {
      setError(e.message || 'Ошибка загрузки пользователей');
    } finally {
      setLoading(false);
    }
  };

  const loadOrganizations = async () => {
    try {
      const data = await apiClient.get<Organization[]>('/api/organizations');
      setOrganizations(data);
    } catch (e: any) {
      console.error('Error loading organizations:', e);
    }
  };

  const loadRoles = async () => {
    try {
      // For now, hardcode roles - you can create an API endpoint later
      setRoles([
        { id: 1, name: 'owner' },
        { id: 2, name: 'admin' },
        { id: 3, name: 'supplier' },
        { id: 4, name: 'ff' },
        { id: 5, name: 'driver' }
      ]);
    } catch (e: any) {
      console.error('Error loading roles:', e);
    }
  };

  const loadFulfillments = async () => {
    try {
      const data = await apiClient.get<Fulfillment[]>('/api/fulfillments');
      setFulfillments(data);
    } catch (e: any) {
      console.error('Error loading fulfillments:', e);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setCreateError('');

    try {
      const payload: any = {
        username: formData.username,
        password: formData.password,
        role_name: formData.role_name,
        organization_id: isOwner ? currentUser.organization_id : formData.organization_id
      };

      // Only include fulfillment_id if it's set and role is ff
      if (formData.role_name === 'ff' && formData.fulfillment_id > 0) {
        payload.fulfillment_id = formData.fulfillment_id;
      }

      await apiClient.post('/api/users', payload);

      // Reset form and close modal
      setFormData({
        username: '',
        password: '',
        role_name: '',
        organization_id: 0,
        fulfillment_id: 0
      });
      setShowCreateForm(false);

      // Reload users
      await loadUsers();
    } catch (e: any) {
      setCreateError(e.message || 'Ошибка создания пользователя');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteClick = (user: User) => {
    setUserToDelete(user);
    setShowDeleteConfirm(true);
  };

  const handleDeleteConfirm = async () => {
    if (!userToDelete) return;

    setDeleting(true);
    try {
      await apiClient.delete(`/api/users/${userToDelete.id}`);

      // Close modal and reset state
      setShowDeleteConfirm(false);
      setUserToDelete(null);

      // Reload users
      await loadUsers();
    } catch (e: any) {
      alert(e.message || 'Ошибка удаления пользователя');
    } finally {
      setDeleting(false);
    }
  };

  const handleDeleteCancel = () => {
    setShowDeleteConfirm(false);
    setUserToDelete(null);
  };

  const handleSearchUsers = async () => {
    if (!searchUsername.trim()) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    setAddError('');
    try {
      const results = await apiClient.get<User[]>(
        `/api/users/search?username=${encodeURIComponent(searchUsername)}`
      );
      setSearchResults(results);
    } catch (e: any) {
      setAddError(e.message || 'Ошибка поиска пользователей');
    } finally {
      setSearching(false);
    }
  };

  const handleAddExistingUser = async () => {
    if (!selectedUser) return;

    setAddingUser(true);
    setAddError('');

    try {
      await apiClient.post('/api/users/add-existing', {
        user_id: selectedUser.id
      });

      // Close modal and reset
      setShowAddExistingForm(false);
      setSearchUsername('');
      setSearchResults([]);
      setSelectedUser(null);

      // Reload users list
      await loadUsers();
    } catch (e: any) {
      setAddError(e.message || 'Ошибка добавления пользователя');
    } finally {
      setAddingUser(false);
    }
  };

  const getRoleLabel = (role: string) => {
    const labels: Record<string, string> = {
      owner: 'Владелец',
      admin: 'Администратор',
      supplier: 'Поставщик',
      ff: 'Фулфилмент',
      driver: 'Водитель'
    };
    return labels[role] || role;
  };

  const isOwner = currentUser?.role === 'owner';
  const isAdmin = currentUser?.role === 'admin';

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-slate-900 mb-2">Пользователи</h1>
          <p className="text-slate-500">Управление пользователями системы</p>
        </div>
        <div className="flex gap-3">
          {isOwner && (
            <button
              onClick={() => setShowAddExistingForm(true)}
              className="flex items-center gap-2 px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition-colors"
            >
              <UsersIcon className="w-4 h-4" />
              Добавить существующего
            </button>
          )}
          <button
            onClick={() => setShowCreateForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Создать пользователя
          </button>
        </div>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader2 className="w-8 h-8 text-primary-500 animate-spin mx-auto mb-4" />
            <p className="text-slate-600">Загрузка пользователей...</p>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="bg-white rounded-2xl shadow-sm border border-red-200 p-12">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <p className="text-slate-900 font-medium mb-2">Ошибка загрузки</p>
            <p className="text-slate-600 mb-4">{error}</p>
            <button
              onClick={loadUsers}
              className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600"
            >
              Попробовать снова
            </button>
          </div>
        </div>
      )}

      {/* Users table */}
      {!loading && !error && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          {users.length === 0 ? (
            <div className="p-12 text-center">
              <UsersIcon className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600 mb-2">Нет пользователей</p>
              <p className="text-sm text-slate-400">Создайте первого пользователя</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-100">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Имя пользователя
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Роль
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Организация
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Фулфилмент
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Действия
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {users.map((user) => (
                    <tr key={user.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900">
                        {user.username}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-700">
                          {getRoleLabel(user.role)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                        {user.organization_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                        {user.fulfillment_name || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                        {currentUser?.id === user.id ? (
                          <span className="text-xs text-slate-400 italic">Вы</span>
                        ) : (
                          <button
                            onClick={() => handleDeleteClick(user)}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                            title={isOwner ? "Убрать из организации" : "Удалить пользователя"}
                          >
                            {isOwner ? (
                              <>
                                <UserX className="w-4 h-4" />
                                Убрать
                              </>
                            ) : (
                              <>
                                <Trash2 className="w-4 h-4" />
                                Удалить
                              </>
                            )}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Create User Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-slate-900">Создать пользователя</h2>
                <button
                  onClick={() => setShowCreateForm(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleCreateUser} className="space-y-4">
                {/* Username */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Имя пользователя
                  </label>
                  <input
                    type="text"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
                    required
                  />
                </div>

                {/* Password */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Пароль
                  </label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
                    required
                    minLength={6}
                  />
                </div>

                {/* Role */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Роль
                  </label>
                  <select
                    value={formData.role_name}
                    onChange={(e) => setFormData({ ...formData, role_name: e.target.value })}
                    className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
                    required
                  >
                    <option value="">Выберите роль</option>
                    {roles.map((role) => (
                      <option key={role.id} value={role.name}>
                        {getRoleLabel(role.name)}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Organization - only shown to admins */}
                {isAdmin && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Организация
                    </label>
                    <select
                      value={formData.organization_id}
                      onChange={(e) => setFormData({ ...formData, organization_id: parseInt(e.target.value) })}
                      className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
                      required
                    >
                      <option value={0}>Выберите организацию</option>
                      {organizations.map((org) => (
                        <option key={org.id} value={org.id}>
                          {org.name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Fulfillment (only for FF role) */}
                {formData.role_name === 'ff' && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Фулфилмент
                    </label>
                    <select
                      value={formData.fulfillment_id}
                      onChange={(e) => setFormData({ ...formData, fulfillment_id: parseInt(e.target.value) })}
                      className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
                    >
                      <option value={0}>Выберите фулфилмент</option>
                      {fulfillments.map((ff) => (
                        <option key={ff.id} value={ff.id}>
                          {ff.name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Error message */}
                {createError && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                    {createError}
                  </div>
                )}

                {/* Buttons */}
                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="flex-1 px-4 py-2 border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
                  >
                    Отмена
                  </button>
                  <button
                    type="submit"
                    disabled={creating}
                    className="flex-1 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors disabled:bg-slate-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {creating ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Создание...
                      </>
                    ) : (
                      'Создать'
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && userToDelete && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
            <div className="flex items-start gap-4 mb-6">
              <div className="flex-shrink-0 w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                <AlertCircle className="w-6 h-6 text-red-600" />
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-slate-900 mb-2">
                  {isOwner ? 'Убрать пользователя из организации?' : 'Удалить пользователя?'}
                </h2>
                <p className="text-sm text-slate-600">
                  {isOwner ? (
                    <>
                      Вы уверены, что хотите убрать пользователя <span className="font-medium text-slate-900">{userToDelete.username}</span> из вашей организации? Пользователь потеряет доступ к данным организации, но останется в системе.
                    </>
                  ) : (
                    <>
                      Вы уверены, что хотите удалить пользователя <span className="font-medium text-slate-900">{userToDelete.username}</span>? Пользователь будет полностью удалён из системы. Это действие нельзя отменить.
                    </>
                  )}
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleDeleteCancel}
                disabled={deleting}
                className="flex-1 px-4 py-2 border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Отмена
              </button>
              <button
                type="button"
                onClick={handleDeleteConfirm}
                disabled={deleting}
                className="flex-1 px-4 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition-colors disabled:bg-red-300 disabled:cursor-not-allowed flex items-center justify-center gap-2 border-2 border-red-700 shadow-sm"
                style={{ backgroundColor: deleting ? '#fca5a5' : '#dc2626', color: '#ffffff' }}
              >
                {deleting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    {isOwner ? 'Удаление...' : 'Удаление...'}
                  </>
                ) : isOwner ? (
                  <>
                    <UserX className="w-4 h-4" />
                    Убрать
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    Удалить
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Existing User Modal */}
      {showAddExistingForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-slate-900">Добавить существующего пользователя</h2>
                <button
                  onClick={() => {
                    setShowAddExistingForm(false);
                    setSearchUsername('');
                    setSearchResults([]);
                    setSelectedUser(null);
                    setAddError('');
                  }}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Search Section */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Поиск по имени пользователя
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={searchUsername}
                    onChange={(e) => setSearchUsername(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearchUsers()}
                    className="flex-1 px-4 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="Введите имя пользователя..."
                  />
                  <button
                    onClick={handleSearchUsers}
                    disabled={searching || !searchUsername.trim()}
                    className="px-6 py-2 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors disabled:bg-slate-300 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    {searching ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Поиск...
                      </>
                    ) : (
                      'Найти'
                    )}
                  </button>
                </div>
              </div>

              {/* Search Results */}
              {searchResults.length > 0 && (
                <div className="mb-6">
                  <label className="block text-sm font-medium text-slate-700 mb-3">
                    Результаты поиска ({searchResults.length})
                  </label>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {searchResults.map((user) => (
                      <div
                        key={user.id}
                        onClick={() => setSelectedUser(user)}
                        className={`p-4 border rounded-xl cursor-pointer transition-all ${
                          selectedUser?.id === user.id
                            ? 'border-primary-500 bg-primary-50'
                            : 'border-slate-200 hover:border-primary-300 hover:bg-slate-50'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium text-slate-900">{user.username}</span>
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-700">
                                {getRoleLabel(user.role)}
                              </span>
                            </div>
                            <div className="text-sm text-slate-600">
                              Организация: {user.organization_name}
                            </div>
                            {user.fulfillment_name && (
                              <div className="text-sm text-slate-600">
                                Фулфилмент: {user.fulfillment_name}
                              </div>
                            )}
                          </div>
                          {selectedUser?.id === user.id && (
                            <CheckCircle2 className="w-5 h-5 text-primary-500" />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* No Results Message */}
              {searchResults.length === 0 && searchUsername && !searching && (
                <div className="mb-6 p-4 bg-slate-50 border border-slate-200 rounded-xl text-center">
                  <p className="text-slate-600">Пользователи не найдены</p>
                </div>
              )}

              {/* Selected User Preview */}
              {selectedUser && (
                <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-green-900 mb-1">
                        Выбран пользователь: {selectedUser.username}
                      </p>
                      <p className="text-sm text-green-700">
                        Роль: {getRoleLabel(selectedUser.role)} • Организация: {selectedUser.organization_name}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Error message */}
              {addError && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-red-700">{addError}</p>
                  </div>
                </div>
              )}

              {/* Buttons */}
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddExistingForm(false);
                    setSearchUsername('');
                    setSearchResults([]);
                    setSelectedUser(null);
                    setAddError('');
                  }}
                  disabled={addingUser}
                  className="flex-1 px-4 py-2 border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Отмена
                </button>
                <button
                  type="button"
                  onClick={handleAddExistingUser}
                  disabled={!selectedUser || addingUser}
                  className="flex-1 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors disabled:bg-slate-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {addingUser ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Добавление...
                    </>
                  ) : (
                    <>
                      <UsersIcon className="w-4 h-4" />
                      Добавить в организацию
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
