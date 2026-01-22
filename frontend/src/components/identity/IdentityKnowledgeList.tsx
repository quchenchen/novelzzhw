import React, { useState, useCallback, useEffect } from 'react';
import {
  Card,
  Space,
  Button,
  Empty,
  List,
  Modal,
  Form,
  Select,
  Input,
  Switch,
  message,
  Popconfirm,
  Tag,
  Tooltip,
  Typography,
} from 'antd';
import {
  EyeOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { identityApi } from '../../services/identityApi';
import type {
  IdentityKnowledge,
  IdentityKnowledgeCreate,
  IdentityKnowledgeUpdate,
  KnowledgeLevel,
} from '../../types/identity';

const { TextArea } = Input;
const { Text } = Typography;

interface IdentityKnowledgeListProps {
  identityId: string;
  characterId: string;
  projectId?: string;
  onRefresh?: () => void;
}

const knowledgeLevelOptions = [
  { label: '完全了解', value: 'full' },
  { label: '部分了解', value: 'partial' },
  { label: '怀疑中', value: 'suspected' },
];

const knowledgeLevelConfig: Record<KnowledgeLevel, { label: string; color: string }> = {
  full: { label: '完全了解', color: 'success' },
  partial: { label: '部分了解', color: 'warning' },
  suspected: { label: '怀疑中', color: 'default' },
};

export const IdentityKnowledgeList: React.FC<IdentityKnowledgeListProps> = ({
  identityId,
  characterId,
  projectId,
  onRefresh,
}) => {
  const [knowledgeList, setKnowledgeList] = useState<IdentityKnowledge[]>([]);
  const [characters, setCharacters] = useState<Array<{ id: string; name: string }>>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingKnowledge, setEditingKnowledge] = useState<IdentityKnowledge | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();

  const fetchKnowledge = useCallback(async () => {
    try {
      setLoading(true);
      const data = await identityApi.getKnowledge(identityId);
      setKnowledgeList(data);
    } catch {
      message.error('获取认知关系失败');
    } finally {
      setLoading(false);
    }
  }, [identityId]);

  const fetchCharacters = useCallback(async () => {
    if (!projectId) return;
    try {
      // const data = await characterApi.getCharacters(projectId);
      // setCharacters(data.filter(c => c.id !== characterId));
      // 临时使用空数据
      setCharacters([]);
    } catch {
      console.error('获取角色列表失败');
    }
  }, [projectId, characterId]);

  useEffect(() => {
    fetchKnowledge();
  }, [fetchKnowledge]);

  useEffect(() => {
    if (isModalOpen) {
      fetchCharacters();
    }
  }, [isModalOpen, fetchCharacters]);

  const handleAdd = useCallback(() => {
    setEditingKnowledge(null);
    form.resetFields();
    form.setFieldsValue({
      knowledge_level: 'partial',
      is_secret: true,
      since_when: '',
    });
    setIsModalOpen(true);
  }, [form]);

  const handleEdit = useCallback((knowledge: IdentityKnowledge) => {
    setEditingKnowledge(knowledge);
    form.setFieldsValue({
      knower_character_id: knowledge.knower_character_id,
      knowledge_level: knowledge.knowledge_level,
      since_when: knowledge.since_when,
      discovered_how: knowledge.discovered_how || '',
      is_secret: knowledge.is_secret,
    });
    setIsModalOpen(true);
  }, [form]);

  const handleDelete = useCallback(async (knowledgeId: string) => {
    try {
      await identityApi.deleteKnowledge(identityId, knowledgeId);
      message.success('删除成功');
      fetchKnowledge();
      onRefresh?.();
    } catch {
      message.error('删除失败');
    }
  }, [identityId, fetchKnowledge, onRefresh]);

  const handleSubmit = useCallback(async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);

      const since_when = values.since_when || '';

      if (editingKnowledge) {
        const updateData: IdentityKnowledgeUpdate = {
          knowledge_level: values.knowledge_level,
          since_when,
          discovered_how: values.discovered_how,
          is_secret: values.is_secret,
        };
        await identityApi.updateKnowledge(identityId, editingKnowledge.id, updateData);
        message.success('更新成功');
      } else {
        const createData: IdentityKnowledgeCreate = {
          knower_character_id: values.knower_character_id,
          knowledge_level: values.knowledge_level,
          since_when,
          discovered_how: values.discovered_how,
          is_secret: values.is_secret,
        };
        await identityApi.addKnowledge(identityId, createData);
        message.success('添加成功');
      }

      setIsModalOpen(false);
      form.resetFields();
      fetchKnowledge();
      onRefresh?.();
    } catch {
      message.error(editingKnowledge ? '更新失败' : '添加失败');
    } finally {
      setSubmitting(false);
    }
  }, [editingKnowledge, form, identityId, fetchKnowledge, onRefresh]);

  return (
    <>
      <Card
        size="small"
        title={
          <Space>
            <EyeOutlined />
            谁知道这个身份
          </Space>
        }
        extra={
          <Button
            size="small"
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            添加认知
          </Button>
        }
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: 20 }}>
            <span style={{ fontSize: 12, color: '#999' }}>加载中...</span>
          </div>
        ) : knowledgeList.length === 0 ? (
          <Empty
            description="暂无认知记录"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <List
            dataSource={knowledgeList}
            renderItem={knowledge => {
              const levelConfig = knowledgeLevelConfig[knowledge.knowledge_level];
              return (
                <List.Item
                  actions={[
                    <Button
                      key="edit"
                      size="small"
                      type="text"
                      icon={<EditOutlined />}
                      onClick={() => handleEdit(knowledge)}
                    />,
                    <Popconfirm
                      key="delete"
                      title="确定删除这条认知记录吗？"
                      onConfirm={() => handleDelete(knowledge.id)}
                      okText="确定"
                      cancelText="取消"
                    >
                      <Button size="small" type="text" danger icon={<DeleteOutlined />} />
                    </Popconfirm>,
                  ]}
                >
                  <List.Item.Meta
                    avatar={<TeamOutlined style={{ fontSize: 18, color: '#52c41a' }} />}
                    title={
                      <Space>
                        <Text strong>{knowledge.knower_name || '未知角色'}</Text>
                        <Tag color={levelConfig.color}>{levelConfig.label}</Tag>
                        {knowledge.is_secret && (
                          <Tag color="purple">保密</Tag>
                        )}
                      </Space>
                    }
                    description={
                      <div>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          知道时间：{knowledge.since_when}
                        </Text>
                        {knowledge.discovered_how && (
                          <Tooltip title={knowledge.discovered_how}>
                            <Text
                              type="secondary"
                              style={{ fontSize: 12, marginLeft: 8 }}
                              ellipsis
                            >
                              发现方式：{knowledge.discovered_how}
                            </Text>
                          </Tooltip>
                        )}
                      </div>
                    }
                  />
                </List.Item>
              );
            }}
          />
        )}
      </Card>

      {/* 添加/编辑认知模态框 */}
      <Modal
        title={editingKnowledge ? '编辑认知' : '添加认知'}
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false);
          form.resetFields();
        }}
        footer={
          <Space>
            <Button onClick={() => setIsModalOpen(false)}>取消</Button>
            <Button type="primary" onClick={handleSubmit} loading={submitting}>
              {editingKnowledge ? '保存' : '添加'}
            </Button>
          </Space>
        }
        centered
        width={500}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          {!editingKnowledge && (
            <Form.Item
              label="选择角色"
              name="knower_character_id"
              rules={[{ required: true, message: '请选择角色' }]}
            >
              <Select
                placeholder="选择知道这个身份的角色"
                showSearch
                optionFilterProp="children"
              >
                {characters.map(char => (
                  <Select.Option key={char.id} value={char.id}>
                    {char.name}
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          )}
          <Form.Item
            label="认知程度"
            name="knowledge_level"
            rules={[{ required: true, message: '请选择认知程度' }]}
          >
            <Select options={knowledgeLevelOptions} />
          </Form.Item>
          <Form.Item
            label="知道时间"
            name="since_when"
            rules={[{ required: true, message: '请选择知道时间' }]}
          >
            <Input placeholder="如：修仙历3001年" />
          </Form.Item>
          <Form.Item label="发现方式" name="discovered_how">
            <TextArea rows={2} placeholder="描述是如何发现这个身份的" />
          </Form.Item>
          <Form.Item
            label="保密"
            name="is_secret"
            valuePropName="checked"
            tooltip="该角色是否会为这个身份保密"
          >
            <Switch checkedChildren="是" unCheckedChildren="否" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default IdentityKnowledgeList;
