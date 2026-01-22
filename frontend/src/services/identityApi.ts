import axios from 'axios';
import type {
  Identity,
  IdentityCreate,
  IdentityUpdate,
  IdentityCareer,
  IdentityCareerCreate,
  IdentityCareerUpdate,
  IdentityKnowledge,
  IdentityKnowledgeCreate,
  IdentityKnowledgeUpdate,
  IdentityListResponse,
  PaginationParams,
  Career,
} from '../types/identity';

// 重新导出 Career 类型供组件使用
export type { Career };

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器：添加认证 token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器：统一错误处理
apiClient.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    const errorMessage = error.response?.data?.detail || error.message || '请求失败';
    console.error('API Error:', errorMessage);
    return Promise.reject(error);
  }
);

export const identityApi = {
  // ==================== Identity CRUD ====================

  /**
   * 获取单个身份
   */
  getById: (id: string): Promise<Identity> => {
    return apiClient.get(`/identities/${id}`);
  },

  /**
   * 按项目获取身份列表
   */
  listByProject: (projectId: string, params?: PaginationParams): Promise<IdentityListResponse> => {
    return apiClient.get(`/identities/project/${projectId}`, { params });
  },

  /**
   * 按角色获取身份列表
   */
  listByCharacter: (characterId: string, params?: PaginationParams): Promise<Identity[]> => {
    return apiClient.get(`/identities/character/${characterId}`, { params });
  },

  /**
   * 创建身份
   */
  create: (data: IdentityCreate): Promise<Identity> => {
    return apiClient.post('/identities', data);
  },

  /**
   * 更新身份
   */
  update: (id: string, data: IdentityUpdate): Promise<Identity> => {
    return apiClient.put(`/identities/${id}`, data);
  },

  /**
   * 删除身份
   */
  delete: (id: string): Promise<{ message: string }> => {
    return apiClient.delete(`/identities/${id}`);
  },

  /**
   * 设置主身份
   */
  setPrimary: (characterId: string, identityId: string): Promise<Identity> => {
    return apiClient.post(`/identities/${identityId}/set-primary`, { character_id: characterId });
  },

  // ==================== Identity Career ====================

  /**
   * 获取身份的所有职业
   */
  getCareers: (identityId: string): Promise<IdentityCareer[]> => {
    return apiClient.get(`/identities/${identityId}/careers`);
  },

  /**
   * 为身份添加职业
   */
  addCareer: (identityId: string, data: IdentityCareerCreate): Promise<IdentityCareer> => {
    return apiClient.post(`/identities/${identityId}/careers`, data);
  },

  /**
   * 更新身份职业进度
   */
  updateCareer: (identityId: string, careerId: string, data: IdentityCareerUpdate): Promise<IdentityCareer> => {
    return apiClient.put(`/identities/${identityId}/careers/${careerId}`, data);
  },

  /**
   * 删除身份职业
   */
  deleteCareer: (identityId: string, careerId: string): Promise<{ message: string }> => {
    return apiClient.delete(`/identities/${identityId}/careers/${careerId}`);
  },

  // ==================== Identity Knowledge ====================

  /**
   * 获取身份的认知关系列表
   */
  getKnowledge: (identityId: string): Promise<IdentityKnowledge[]> => {
    return apiClient.get(`/identities/${identityId}/knowledge`);
  },

  /**
   * 添加认知关系
   */
  addKnowledge: (identityId: string, data: IdentityKnowledgeCreate): Promise<IdentityKnowledge> => {
    return apiClient.post(`/identities/${identityId}/knowledge`, data);
  },

  /**
   * 更新认知关系
   */
  updateKnowledge: (identityId: string, knowledgeId: string, data: IdentityKnowledgeUpdate): Promise<IdentityKnowledge> => {
    return apiClient.put(`/identities/${identityId}/knowledge/${knowledgeId}`, data);
  },

  /**
   * 删除认知关系
   */
  deleteKnowledge: (identityId: string, knowledgeId: string): Promise<{ message: string }> => {
    return apiClient.delete(`/identities/${identityId}/knowledge/${knowledgeId}`);
  },

  /**
   * 检查角色是否知道某个身份
   */
  checkKnowledge: (identityId: string, knowerCharacterId: string): Promise<{
    knows: boolean;
    knowledge_level?: string;
    knowledge?: IdentityKnowledge;
  }> => {
    return apiClient.get(`/identities/${identityId}/knowledge/check`, {
      params: { knower_character_id: knowerCharacterId }
    });
  },
};

export default identityApi;
