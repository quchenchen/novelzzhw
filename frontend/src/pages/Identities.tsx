import { useState, useEffect } from 'react';
import {
  Button,
  message,
  Row,
  Col,
  Empty,
  Typography,
  Space,
  Tabs,
  Card
} from 'antd';
import { PlusOutlined, UserOutlined, CrownOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useStore } from '../store';
import { identityApi } from '../services/identityApi';
import { IdentityForm } from '../components/identity/IdentityForm';
import { IdentityCareerCard } from '../components/identity/IdentityCareerCard';
import { IdentityKnowledgeList } from '../components/identity/IdentityKnowledgeList';
import type { Identity } from '../types/identity';

const { Title } = Typography;

interface CharacterWithIdentities {
  id: string;
  name: string;
  role_type: string;
  personalities?: string;
  appearance?: string;
  identities: Identity[];
}

export default function Identities() {
  const { currentProject } = useStore();
  const [charactersWithIdentities, setCharactersWithIdentities] = useState<CharacterWithIdentities[]>([]);
  const [selectedCharacter, setSelectedCharacter] = useState<CharacterWithIdentities | null>(null);
  const [selectedIdentity, setSelectedIdentity] = useState<Identity | null>(null);
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [editingIdentity, setEditingIdentity] = useState<Identity | null>(null);

  // 获取项目内所有角色的身份
  const fetchIdentities = async () => {
    if (!currentProject?.id) return;

    try {
      // 获取所有角色
      const charactersRes = await fetch(`${import.meta.env.VITE_API_BASE_URL || ''}/api/characters/project/${currentProject.id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      const charactersData = await charactersRes.json();

      // 为每个角色获取身份
      const charactersWithIds = await Promise.all(
        charactersData.map(async (char: any) => {
          try {
            const identitiesRes = await fetch(
            `${import.meta.env.VITE_API_BASE_URL || ''}/api/identities/character/${char.id}`,
            {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
              },
            }
          );
            const identities = await identitiesRes.json();
            return {
              ...char,
              identities: identities || [],
            };
          } catch {
            return {
              ...char,
              identities: [],
            };
          }
        })
      );

      // 过滤出有身份的角色
      const withIdentities = charactersWithIds.filter((c) => c.identities.length > 0);
      setCharactersWithIdentities(withIdentities);

      // 默认选择第一个有身份的角色
      if (withIdentities.length > 0 && !selectedCharacter) {
        setSelectedCharacter(withIdentities[0]);
        if (withIdentities[0].identities.length > 0) {
          setSelectedIdentity(withIdentities[0].identities[0]);
        }
      }
    } catch (error) {
      console.error('获取角色身份失败:', error);
      message.error('获取身份信息失败');
    }
  };

  useEffect(() => {
    fetchIdentities();
  }, [currentProject?.id]);

  // 创建新身份
  const handleCreateIdentity = async (characterId: string, values: any) => {
    try {
      await identityApi.create({
        character_id: characterId,
        ...values,
      });
      message.success('身份创建成功');
      await fetchIdentities();
    } catch (error) {
      message.error('创建身份失败');
      throw error;
    }
  };

  // 更新身份
  const handleUpdateIdentity = async (identity: Identity, values: any) => {
    try {
      await identityApi.update(identity.id, values);
      message.success('身份更新成功');
      await fetchIdentities();
    } catch (error) {
      message.error('更新身份失败');
      throw error;
    }
  };

  // 删除身份
  const handleDeleteIdentity = async (identityId: string) => {
    try {
      await identityApi.delete(identityId);
      message.success('身份删除成功');
      setSelectedIdentity(null);
      await fetchIdentities();
    } catch (error) {
      message.error('删除身份失败');
    }
  };

  // 设置主身份
  const handleSetPrimary = async (characterId: string, identityId: string) => {
    try {
      await identityApi.setPrimary(characterId, identityId);
      message.success('已设置为主身份');
      await fetchIdentities();
    } catch (error) {
      message.error('设置失败');
    }
  };

  // 打开身份表单
  const openFormModal = () => {
    setEditingIdentity(null);
    setIsFormModalOpen(true);
  };

  // 选择身份
  const handleSelectIdentity = (identity: Identity) => {
    setSelectedIdentity(identity);
  };

  if (!currentProject) return null;

  return (
    <div style={{ padding: '24px', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <UserOutlined style={{ marginRight: 8 }} />
          分身设定管理
        </Title>
        <div style={{ marginTop: 8, color: '#666' }}>
          为角色创建多个身份，用于卧底、伪装等复杂剧情设定
        </div>
      </div>

      {charactersWithIdentities.length === 0 ? (
        <Empty
          description="还没有角色拥有分身设定"
          style={{ marginTop: 60 }}
        />
      ) : (
        <Row gutter={24}>
          {/* 左侧：角色列表 */}
          <Col span={8}>
            <Card title="拥有分身的角色" bordered={false}>
              {charactersWithIdentities.map((char) => (
                <div
                  key={char.id}
                  onClick={() => setSelectedCharacter(char)}
                  style={{
                    padding: '12px',
                    marginBottom: '8px',
                    cursor: 'pointer',
                    borderRadius: '4px',
                    background: selectedCharacter?.id === char.id ? '#f0f5ff' : 'transparent',
                    border: selectedCharacter?.id === char.id ? '1px solid #1890ff' : '1px solid transparent',
                  }}
                >
                  <div style={{ fontWeight: 500, marginBottom: 4 }}>
                    {char.name}
                  </div>
                  <div style={{ fontSize: 12, color: '#999' }}>
                    {char.identities.length} 个身份
                  </div>
                </div>
              ))}
            </Card>
          </Col>

          {/* 右侧：身份详情 */}
          <Col span={16}>
            {selectedCharacter ? (
              <>
                <div
                  style={{
                    marginBottom: 16,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <Title level={4} style={{ margin: 0 }}>
                    {selectedCharacter.name} 的身份
                  </Title>
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => openFormModal()}
                    size="small"
                  >
                    新建身份
                  </Button>
                </div>

                {selectedCharacter.identities.length === 0 ? (
                  <Empty description="该角色暂无身份" />
                ) : (
                  <Row gutter={[16, 16]}>
                    {selectedCharacter.identities.map((identity) => (
                      <Col xs={24} sm={12} key={identity.id}>
                        <div
                          onClick={() => handleSelectIdentity(identity)}
                          style={{
                            cursor: 'pointer',
                            border: selectedIdentity?.id === identity.id
                              ? '2px solid #1890ff'
                              : '1px solid #d9d9d9',
                            borderRadius: '8px',
                            padding: '16px',
                            background: selectedIdentity?.id === identity.id
                              ? '#f0f5ff'
                              : '#fff',
                          }}
                        >
                        <div
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            marginBottom: 12,
                          }}
                        >
                          <Space>
                            {identity.is_primary && (
                              <span
                                style={{
                                  background: '#ffd666',
                                  padding: '2px 8px',
                                  borderRadius: '4px',
                                  fontSize: 12,
                                  fontWeight: 500,
                                }}
                              >
                                <CrownOutlined
                                  style={{ fontSize: 10, marginRight: 4 }}
                                />
                                主身份
                              </span>
                            )}
                            <span
                              style={{
                                padding: '2px 8px',
                                borderRadius: '4px',
                                fontSize: 12,
                                fontWeight: 500,
                              }}
                            >
                              {identity.identity_type === 'real' && '真身'}
                              {identity.identity_type === 'public' && '公开'}
                              {identity.identity_type === 'secret' && '隐藏'}
                              {identity.identity_type === 'disguise' && '伪装'}
                            </span>
                          </Space>
                          <Space size="small">
                            {!identity.is_primary && (
                              <Button
                                type="link"
                                size="small"
                                icon={<CrownOutlined />}
                                onClick={() => handleSetPrimary(selectedCharacter.id, identity.id)}
                              >
                                设为主
                              </Button>
                            )}
                            <Button
                              type="link"
                              size="small"
                              icon={<EditOutlined />}
                              onClick={() => {
                                setEditingIdentity(identity);
                                setIsFormModalOpen(true);
                              }}
                            />
                            <Button
                              type="link"
                              danger
                              size="small"
                              icon={<DeleteOutlined />}
                              onClick={() => handleDeleteIdentity(identity.id)}
                            />
                          </Space>
                        </div>

                        <div style={{ marginBottom: 12 }}>
                          <div
                            style={{
                              fontSize: 16,
                              fontWeight: 500,
                              marginBottom: 4,
                            }}
                          >
                            {identity.name}
                          </div>
                          {identity.appearance && (
                            <div
                              style={{
                                fontSize: 12,
                                color: '#666',
                                marginBottom: 4,
                              }}
                            >
                              {identity.appearance}
                            </div>
                          )}
                          {identity.personality && (
                            <div
                              style={{
                                fontSize: 12,
                                color: '#666',
                                marginBottom: 4,
                              }}
                            >
                              {identity.personality}
                            </div>
                          )}
                          {identity.background && (
                            <div
                              style={{
                                fontSize: 12,
                                color: '#666',
                              fontStyle: 'italic',
                              overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                display: '-webkit-box',
                                WebkitLineClamp: 2,
                              }}
                            >
                              {identity.background}
                            </div>
                          )}
                        </div>

                        <div
                          style={{
                            borderTop: '1px solid #f0f0f0',
                            paddingTop: '12px',
                          }}
                        >
                          <Tabs
                            defaultActiveKey="careers"
                            size="small"
                            items={[
                              {
                                key: 'careers',
                                label: '职业',
                                children: (
                                  <IdentityCareerCard
                                    identityId={identity.id}
                                    onRefresh={fetchIdentities}
                                  />
                                ),
                              },
                              {
                                key: 'knowledge',
                                label: '谁知晓',
                                children: (
                                  <IdentityKnowledgeList
                                    identityId={identity.id}
                                    characterId={selectedCharacter.id}
                                    onRefresh={fetchIdentities}
                                  />
                                ),
                              },
                            ]}
                          />
                        </div>
                        </div>
                      </Col>
                    ))}
                  </Row>
                )}
              </>
            ) : (
              <Empty description="请选择一个角色查看其身份" />
            )}
          </Col>
        </Row>
      )}

      {/* 创建/编辑身份表单 */}
      <IdentityForm
        open={isFormModalOpen}
        onClose={() => {
          setIsFormModalOpen(false);
          setEditingIdentity(null);
        }}
        onSubmit={async (values: any) => {
          if (editingIdentity) {
            await handleUpdateIdentity(editingIdentity, values);
          } else {
            await handleCreateIdentity(selectedCharacter!.id, values);
          }
          setIsFormModalOpen(false);
          setEditingIdentity(null);
        }}
        identity={editingIdentity || undefined}
      />
    </div>
  );
}
