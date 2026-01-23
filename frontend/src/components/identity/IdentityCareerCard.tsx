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
  InputNumber,
  Input,
  message,
  Popconfirm,
  Tag,
  Progress,
  Typography,
} from 'antd';
import {
  TrophyOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  MedicineBoxOutlined,
} from '@ant-design/icons';
import { identityApi } from '../../services/identityApi';
import type { IdentityCareer, IdentityCareerCreate, IdentityCareerUpdate } from '../../types/identity';

const { TextArea } = Input;
const { Text } = Typography;

interface IdentityCareerCardProps {
  identityId: string;
  onRefresh?: () => void;
}

export const IdentityCareerCard: React.FC<IdentityCareerCardProps> = ({
  identityId,
  onRefresh,
}) => {
  const [careers, setCareers] = useState<IdentityCareer[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCareer, setEditingCareer] = useState<IdentityCareer | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();

  const fetchCareers = useCallback(async () => {
    try {
      setLoading(true);
      const data = await identityApi.getCareers(identityId);
      setCareers(data);
    } catch {
      message.error('获取职业信息失败');
    } finally {
      setLoading(false);
    }
  }, [identityId]);

  useEffect(() => {
    fetchCareers();
  }, [fetchCareers]);

  const handleAdd = useCallback(() => {
    setEditingCareer(null);
    form.resetFields();
    form.setFieldsValue({
      career_type: 'sub',
      current_stage: 1,
      stage_progress: 0,
    });
    setIsModalOpen(true);
  }, [form]);

  const handleEdit = useCallback((career: IdentityCareer) => {
    setEditingCareer(career);
    form.setFieldsValue({
      career_id: career.career_id,
      career_type: career.career_type,
      current_stage: career.current_stage,
      stage_progress: career.stage_progress,
      started_at: career.started_at,
      reached_current_stage_at: career.reached_current_stage_at,
      notes: career.notes || '',
    });
    setIsModalOpen(true);
  }, [form]);

  const handleDelete = useCallback(async (careerId: string) => {
    try {
      await identityApi.deleteCareer(identityId, careerId);
      message.success('删除成功');
      fetchCareers();
      onRefresh?.();
    } catch {
      message.error('删除失败');
    }
  }, [identityId, fetchCareers, onRefresh]);

  const handleSubmit = useCallback(async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);

      if (editingCareer) {
        const updateData: IdentityCareerUpdate = {
          current_stage: values.current_stage,
          stage_progress: values.stage_progress,
          started_at: values.started_at,
          reached_current_stage_at: values.reached_current_stage_at,
          notes: values.notes,
        };
        await identityApi.updateCareer(identityId, editingCareer.career_id, updateData);
        message.success('更新成功');
      } else {
        const createData: IdentityCareerCreate = {
          career_id: values.career_id,
          career_type: values.career_type,
          current_stage: values.current_stage,
          stage_progress: values.stage_progress,
          started_at: values.started_at,
          reached_current_stage_at: values.reached_current_stage_at,
          notes: values.notes,
        };
        await identityApi.addCareer(identityId, createData);
        message.success('添加成功');
      }

      setIsModalOpen(false);
      form.resetFields();
      fetchCareers();
      onRefresh?.();
    } catch {
      message.error(editingCareer ? '更新失败' : '添加失败');
    } finally {
      setSubmitting(false);
    }
  }, [editingCareer, form, identityId, fetchCareers, onRefresh]);

  const getCareerTypeColor = (type: string) => {
    return type === 'main' ? 'blue' : 'green';
  };

  const getCareerTypeLabel = (type: string) => {
    return type === 'main' ? '主' : '副';
  };

  return (
    <>
      <Card
        size="small"
        title={
          <Space>
            <MedicineBoxOutlined />
            职业信息
          </Space>
        }
        extra={
          <Button
            size="small"
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            添加职业
          </Button>
        }
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: 20 }}>
            <span style={{ fontSize: 12, color: '#999' }}>加载中...</span>
          </div>
        ) : careers.length === 0 ? (
          <Empty
            description="暂无职业"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <List
            dataSource={careers}
            renderItem={career => (
              <List.Item
                actions={[
                  <Button
                    key="edit"
                    size="small"
                    type="text"
                    icon={<EditOutlined />}
                    onClick={() => handleEdit(career)}
                  />,
                  <Popconfirm
                    key="delete"
                    title="确定删除这个职业吗？"
                    onConfirm={() => handleDelete(career.career_id)}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button size="small" type="text" danger icon={<DeleteOutlined />} />
                  </Popconfirm>,
                ]}
              >
                <List.Item.Meta
                  avatar={<TrophyOutlined style={{ fontSize: 20, color: '#1890ff' }} />}
                  title={
                    <Space>
                      <Text strong>{career.career_name || '未知职业'}</Text>
                      <Tag color={getCareerTypeColor(career.career_type)}>
                        {getCareerTypeLabel(career.career_type)}
                      </Tag>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        阶段 {career.current_stage}/{career.career_max_stage || '?'}
                      </Text>
                    </Space>
                  }
                  description={
                    <div>
                      <Progress
                        percent={career.stage_progress}
                        size="small"
                        style={{ marginBottom: 4 }}
                      />
                      {career.notes && (
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {career.notes}
                        </Text>
                      )}
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Card>

      {/* 添加/编辑职业模态框 */}
      <Modal
        title={editingCareer ? '编辑职业' : '添加职业'}
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false);
          form.resetFields();
        }}
        footer={
          <Space>
            <Button onClick={() => setIsModalOpen(false)}>取消</Button>
            <Button type="primary" onClick={handleSubmit} loading={submitting}>
              {editingCareer ? '保存' : '添加'}
            </Button>
          </Space>
        }
        centered
        width={500}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          {!editingCareer && (
            <Form.Item
              label="职业ID"
              name="career_id"
              rules={[{ required: true, message: '请输入职业ID' }]}
            >
              <Input placeholder="请输入职业ID" />
            </Form.Item>
          )}
          <Form.Item
            label="职业类型"
            name="career_type"
            rules={[{ required: true, message: '请选择职业类型' }]}
          >
            <Select>
              <Select.Option value="main">主职业</Select.Option>
              <Select.Option value="sub">副职业</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item
            label="当前阶段"
            name="current_stage"
            rules={[{ required: true, message: '请输入当前阶段' }]}
          >
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            label="阶段进度（0-100）"
            name="stage_progress"
            rules={[{ required: true, message: '请输入阶段进度' }]}
          >
            <InputNumber min={0} max={100} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="开始时间" name="started_at">
            <Input placeholder="如：修仙历3000年" />
          </Form.Item>
          <Form.Item label="到达当前阶段时间" name="reached_current_stage_at">
            <Input placeholder="如：修仙历3001年" />
          </Form.Item>
          <Form.Item label="备注" name="notes">
            <TextArea rows={2} placeholder="如：突破至金丹期" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default IdentityCareerCard;
