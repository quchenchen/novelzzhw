import React from 'react';
import { Card, Space, Tag, Typography, Popconfirm, Button, Tooltip } from 'antd';
import { EditOutlined, DeleteOutlined, UserOutlined, CrownOutlined, EyeInvisibleOutlined, MaskOutlined } from '@ant-design/icons';
import { cardStyles } from '../CardStyles';
import type { Identity, IdentityType, IdentityStatus } from '../../types/identity';

const { Text, Paragraph } = Typography;

interface IdentityCardProps {
  identity: Identity;
  onEdit?: (identity: Identity) => void;
  onDelete?: (id: string) => void;
  onSetPrimary?: (id: string) => void;
}

const identityTypeConfig: Record<IdentityType, { label: string; color: string; icon: React.ReactNode }> = {
  real: { label: '真身', color: 'blue', icon: <UserOutlined /> },
  public: { label: '公开', color: 'green', icon: <UserOutlined /> },
  secret: { label: '隐藏', color: 'purple', icon: <EyeInvisibleOutlined /> },
  disguise: { label: '伪装', color: 'orange', icon: <MaskOutlined /> },
};

const statusConfig: Record<IdentityStatus, { label: string; color: string }> = {
  active: { label: '活跃', color: 'success' },
  inactive: { label: '失效', color: 'default' },
  burned: { label: '暴露', color: 'error' },
};

export const IdentityCard: React.FC<IdentityCardProps> = ({
  identity,
  onEdit,
  onDelete,
  onSetPrimary,
}) => {
  const typeConfig = identityTypeConfig[identity.identity_type];
  const statusConfigItem = statusConfig[identity.status];

  const actions: React.ReactNode[] = [];

  if (onEdit) {
    actions.push(
      <EditOutlined key="edit" onClick={() => onEdit(identity)} />
    );
  }

  if (onSetPrimary && !identity.is_primary) {
    actions.push(
      <Tooltip key="primary" title="设为主身份">
        <CrownOutlined onClick={() => onSetPrimary(identity.id)} />
      </Tooltip>
    );
  }

  if (onDelete) {
    actions.push(
      <Popconfirm
        key="delete"
        title="确定删除这个身份吗？"
        description="删除后无法恢复，关联的职业和认知关系也将被删除。"
        onConfirm={() => onDelete(identity.id)}
        okText="确定"
        cancelText="取消"
      >
        <DeleteOutlined />
      </Popconfirm>
    );
  }

  return (
    <Card
      hoverable
      style={{
        ...cardStyles.character,
        borderColor: typeConfig.color,
      }}
      styles={{
        body: {
          flex: 1,
          overflow: 'auto',
          display: 'flex',
          flexDirection: 'column',
        },
        actions: {
          borderRadius: '0 0 12px 12px',
        },
      }}
      actions={actions.length > 0 ? actions : undefined}
    >
      <Card.Meta
        avatar={
          <div style={{ fontSize: 32, color: `var(--color-${typeConfig.color})` }}>
            {typeConfig.icon}
          </div>
        }
        title={
          <Space>
            <span style={cardStyles.ellipsis}>{identity.name}</span>
            {identity.is_primary && (
              <Tag color="gold" icon={<CrownOutlined />}>
                主身份
              </Tag>
            )}
            <Tag color={typeConfig.color}>{typeConfig.label}</Tag>
            <Tag color={statusConfigItem.color}>{statusConfigItem.label}</Tag>
          </Space>
        }
        description={
          <div style={cardStyles.description}>
            {identity.appearance && (
              <div style={{ marginBottom: 8 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>外貌：</Text>
                <Paragraph
                  style={{ fontSize: 13, marginBottom: 0 }}
                  ellipsis={{ tooltip: identity.appearance, rows: 2 }}
                >
                  {identity.appearance}
                </Paragraph>
              </div>
            )}
            {identity.personality && (
              <div style={{ marginBottom: 8 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>性格：</Text>
                <Paragraph
                  style={{ fontSize: 13, marginBottom: 0 }}
                  ellipsis={{ tooltip: identity.personality, rows: 2 }}
                >
                  {identity.personality}
                </Paragraph>
              </div>
            )}
            {identity.voice_style && (
              <div style={{ marginBottom: 8 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>说话风格：</Text>
                <Paragraph
                  style={{ fontSize: 13, marginBottom: 0 }}
                  ellipsis={{ tooltip: identity.voice_style, rows: 2 }}
                >
                  {identity.voice_style}
                </Paragraph>
              </div>
            )}
            {identity.background && (
              <div style={{ marginTop: 12 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>背景：</Text>
                <Paragraph
                  type="secondary"
                  style={{ fontSize: 12, marginBottom: 0 }}
                  ellipsis={{ tooltip: identity.background, rows: 3 }}
                >
                  {identity.background}
                </Paragraph>
              </div>
            )}
          </div>
        }
      />
    </Card>
  );
};

export default IdentityCard;
