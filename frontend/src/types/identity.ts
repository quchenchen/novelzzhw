// 身份类型定义
export type IdentityType = 'real' | 'public' | 'secret' | 'disguise';
export type IdentityStatus = 'active' | 'inactive' | 'burned';
export type KnowledgeLevel = 'full' | 'partial' | 'suspected';

// 身份
export interface Identity {
  id: string;
  project_id: string;
  character_id: string;
  name: string;
  identity_type: IdentityType;
  is_primary: boolean;
  appearance?: string;
  personality?: string;
  background?: string;
  voice_style?: string;
  status: IdentityStatus;
  created_at: string;
  updated_at: string;
}

// 身份创建
export interface IdentityCreate {
  character_id: string;
  name: string;
  identity_type: IdentityType;
  is_primary?: boolean;
  appearance?: string;
  personality?: string;
  background?: string;
  voice_style?: string;
  status?: IdentityStatus;
}

// 身份更新
export interface IdentityUpdate {
  name?: string;
  identity_type?: IdentityType;
  is_primary?: boolean;
  appearance?: string;
  personality?: string;
  background?: string;
  voice_style?: string;
  status?: IdentityStatus;
}

// 身份职业关联
export interface IdentityCareer {
  id: string;
  identity_id: string;
  career_id: string;
  career_type: 'main' | 'sub';
  current_stage: number;
  stage_progress: number;
  started_at: string;
  reached_current_stage_at: string;
  career_name?: string;
  career_max_stage?: number;
  notes?: string;
}

// 身份职业创建
export interface IdentityCareerCreate {
  career_id: string;
  career_type: 'main' | 'sub';
  current_stage?: number;
  stage_progress?: number;
  started_at?: string;
  reached_current_stage_at?: string;
  notes?: string;
}

// 身份职业更新
export interface IdentityCareerUpdate {
  current_stage?: number;
  stage_progress?: number;
  started_at?: string;
  reached_current_stage_at?: string;
  notes?: string;
}

// 身份认知关系
export interface IdentityKnowledge {
  id: string;
  identity_id: string;
  knower_character_id: string;
  knowledge_level: KnowledgeLevel;
  since_when: string;
  discovered_how?: string;
  is_secret: boolean;
  created_at: string;
  knower_name?: string;
}

// 身份认知创建
export interface IdentityKnowledgeCreate {
  knower_character_id: string;
  knowledge_level: KnowledgeLevel;
  since_when: string;
  discovered_how?: string;
  is_secret?: boolean;
}

// 身份认知更新
export interface IdentityKnowledgeUpdate {
  knowledge_level?: KnowledgeLevel;
  since_when?: string;
  discovered_how?: string;
  is_secret?: boolean;
}

// 身份列表响应
export interface IdentityListResponse {
  total: number;
  items: Identity[];
}

// 分页参数
export interface PaginationParams {
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// 职业类型（用于职业选择器）
export interface Career {
  id: string;
  name: string;
  type: 'main' | 'sub';
  max_stage: number;
}
