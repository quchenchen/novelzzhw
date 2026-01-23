import React from 'react';
import { Modal, Form, Input, Select, Switch, Space, Button, Row, Col } from 'antd';
import type { Identity, IdentityCreate, IdentityUpdate } from '../../types/identity';

const { TextArea } = Input;

interface IdentityFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: IdentityCreate | IdentityUpdate) => Promise<void>;
  identity?: Identity;
  loading?: boolean;
}

const identityTypeOptions = [
  { label: '真身', value: 'real' },
  { label: '公开', value: 'public' },
  { label: '隐藏', value: 'secret' },
  { label: '伪装', value: 'disguise' },
];

const statusOptions = [
  { label: '活跃', value: 'active' },
  { label: '失效', value: 'inactive' },
  { label: '暴露', value: 'burned' },
];

export const IdentityForm: React.FC<IdentityFormProps> = ({
  open,
  onClose,
  onSubmit,
  identity,
  loading = false,
}) => {
  const [form] = Form.useForm();

  const isEdit = !!identity;

  React.useEffect(() => {
    if (open) {
      if (identity) {
        form.setFieldsValue({
          name: identity.name,
          identity_type: identity.identity_type,
          is_primary: identity.is_primary,
          appearance: identity.appearance || '',
          personality: identity.personality || '',
          background: identity.background || '',
          voice_style: identity.voice_style || '',
          status: identity.status,
        });
      } else {
        form.resetFields();
        form.setFieldsValue({
          identity_type: 'public',
          is_primary: false,
          status: 'active',
        });
      }
    }
  }, [open, identity, form]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      await onSubmit(values);
      form.resetFields();
    } catch (error) {
      // Form validation failed or submit failed
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onClose();
  };

  return (
    <Modal
      title={isEdit ? '编辑身份' : '创建身份'}
      open={open}
      onCancel={handleCancel}
      footer={
        <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
          <Button onClick={handleCancel}>取消</Button>
          <Button type="primary" onClick={handleSubmit} loading={loading}>
            {isEdit ? '保存' : '创建'}
          </Button>
        </Space>
      }
      centered
      width={600}
      styles={{
        body: {
          maxHeight: 'calc(100vh - 200px)',
          overflowY: 'auto',
        },
      }}
    >
      <Form
        form={form}
        layout="vertical"
        style={{ marginTop: 16 }}
      >
        {/* 第一行：名称、类型、主身份 */}
        <Row gutter={12}>
          <Col span={12}>
            <Form.Item
              label="身份名称"
              name="name"
              rules={[{ required: true, message: '请输入身份名称' }]}
            >
              <Input placeholder="如：张三、蒙面黑衣人" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label="身份类型"
              name="identity_type"
              rules={[{ required: true, message: '请选择身份类型' }]}
            >
              <Select
                placeholder="选择身份类型"
                options={identityTypeOptions}
              />
            </Form.Item>
          </Col>
        </Row>

        {/* 第二行：主身份、状态 */}
        <Row gutter={12}>
          <Col span={12}>
            <Form.Item
              label="主身份"
              name="is_primary"
              valuePropName="checked"
              tooltip="角色的主身份，用于默认显示"
            >
              <Switch checkedChildren="是" unCheckedChildren="否" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label="状态"
              name="status"
              rules={[{ required: true, message: '请选择状态' }]}
            >
              <Select
                placeholder="选择状态"
                options={statusOptions}
              />
            </Form.Item>
          </Col>
        </Row>

        {/* 外貌描写 */}
        <Form.Item
          label="外貌描写"
          name="appearance"
          tooltip="描述该身份的外貌特征"
        >
          <TextArea
            rows={2}
            placeholder="描述该身份的外貌特征，如身材、衣着、面容等..."
          />
        </Form.Item>

        {/* 性格特点 */}
        <Form.Item
          label="性格特点"
          name="personality"
          tooltip="该身份下的性格表现"
        >
          <TextArea
            rows={2}
            placeholder="描述该身份下的性格特点，可以与真身不同..."
          />
        </Form.Item>

        {/* 说话风格 */}
        <Form.Item
          label="说话风格"
          name="voice_style"
          tooltip="该身份的说话语气、用词习惯等"
        >
          <TextArea
            rows={2}
            placeholder="描述该身份的说话风格，如语气、口癖、用词习惯..."
          />
        </Form.Item>

        {/* 背景设定 */}
        <Form.Item
          label="背景设定"
          name="background"
          tooltip="该身份的背景故事，如何形成这个身份的"
        >
          <TextArea
            rows={3}
            placeholder="描述该身份的背景故事，如何获得或形成这个身份的..."
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default IdentityForm;
