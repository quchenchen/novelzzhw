import React, { useState, useCallback } from 'react';
import { Card, Space, Button, Empty, Row, Col, Modal, message, Spin } from 'antd';
import { PlusOutlined, UnorderedListOutlined } from '@ant-design/icons';
import { IdentityCard } from './IdentityCard';
import { IdentityForm } from './IdentityForm';
import { IdentityCareerCard } from './IdentityCareerCard';
import { IdentityKnowledgeList } from './IdentityKnowledgeList';
import type { Identity, IdentityCreate, IdentityUpdate } from '../../types/identity';

interface IdentityListProps {
  characterId: string;
  identities: Identity[];
  loading?: boolean;
  onCreate?: (data: IdentityCreate) => Promise<void>;
  onUpdate?: (id: string, data: IdentityUpdate) => Promise<void>;
  onDelete?: (id: string) => Promise<void>;
  onSetPrimary?: (id: string) => Promise<void>;
  onRefresh?: () => Promise<void>;
}

export const IdentityList: React.FC<IdentityListProps> = ({
  characterId,
  identities,
  loading = false,
  onCreate,
  onUpdate,
  onDelete,
  onSetPrimary,
  onRefresh,
}) => {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingIdentity, setEditingIdentity] = useState<Identity | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [selectedIdentity, setSelectedIdentity] = useState<Identity | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  const handleCreate = useCallback(async () => {
    if (!onCreate) return;
    setIsFormOpen(true);
  }, [onCreate]);

  const handleEdit = useCallback(async (identity: Identity) => {
    setEditingIdentity(identity);
    setIsFormOpen(true);
  }, []);

  const handleDelete = useCallback(async (id: string) => {
    if (!onDelete) return;
    try {
      await onDelete(id);
      message.success('删除成功');
      onRefresh?.();
    } catch {
      message.error('删除失败');
    }
  }, [onDelete, onRefresh]);

  const handleSetPrimary = useCallback(async (id: string) => {
    if (!onSetPrimary) return;
    try {
      await onSetPrimary(id);
      message.success('已设置为主身份');
      onRefresh?.();
    } catch {
      message.error('设置失败');
    }
  }, [onSetPrimary, onRefresh]);

  const handleFormSubmit = useCallback(async (data: IdentityCreate | IdentityUpdate) => {
    setSubmitting(true);
    try {
      if (editingIdentity) {
        await onUpdate?.(editingIdentity.id, data);
        message.success('更新成功');
      } else {
        await onCreate?.({ ...data, character_id: characterId } as IdentityCreate);
        message.success('创建成功');
      }
      setIsFormOpen(false);
      setEditingIdentity(null);
      onRefresh?.();
    } catch {
      message.error(editingIdentity ? '更新失败' : '创建失败');
    } finally {
      setSubmitting(false);
    }
  }, [characterId, editingIdentity, onCreate, onUpdate, onRefresh]);

  const handleFormClose = useCallback(() => {
    setIsFormOpen(false);
    setEditingIdentity(null);
  }, []);

  const handleShowDetail = useCallback((identity: Identity) => {
    setSelectedIdentity(identity);
    setIsDetailModalOpen(true);
  }, []);

  const primaryIdentity = identities.find(i => i.is_primary);
  const otherIdentities = identities.filter(i => !i.is_primary);

  return (
    <>
      <Card
        title={
          <Space>
            <UnorderedListOutlined />
            身份管理
          </Space>
        }
        extra={
          onCreate && (
            <Button
              type="primary"
              size="small"
              icon={<PlusOutlined />}
              onClick={handleCreate}
            >
              添加身份
            </Button>
          )
        }
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin />
          </div>
        ) : identities.length === 0 ? (
          <Empty
            description="暂无身份"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <Row gutter={[12, 12]}>
            {/* 主身份 */}
            {primaryIdentity && (
              <Col xs={24} sm={12} md={8}>
                <div onClick={() => handleShowDetail(primaryIdentity)} style={{ cursor: 'pointer' }}>
                  <IdentityCard
                    identity={primaryIdentity}
                    onEdit={onUpdate ? handleEdit : undefined}
                    onDelete={onDelete ? handleDelete : undefined}
                  />
                </div>
              </Col>
            )}
            {/* 其他身份 */}
            {otherIdentities.map(identity => (
              <Col key={identity.id} xs={24} sm={12} md={8}>
                <div onClick={() => handleShowDetail(identity)} style={{ cursor: 'pointer' }}>
                  <IdentityCard
                    identity={identity}
                    onEdit={onUpdate ? handleEdit : undefined}
                    onDelete={onDelete ? handleDelete : undefined}
                    onSetPrimary={onSetPrimary ? handleSetPrimary : undefined}
                  />
                </div>
              </Col>
            ))}
          </Row>
        )}
      </Card>

      {/* 创建/编辑表单 */}
      <IdentityForm
        open={isFormOpen}
        identity={editingIdentity ?? undefined}
        onClose={handleFormClose}
        onSubmit={handleFormSubmit}
        loading={submitting}
      />

      {/* 身份详情模态框 */}
      <Modal
        title={selectedIdentity?.name || '身份详情'}
        open={isDetailModalOpen}
        onCancel={() => {
          setIsDetailModalOpen(false);
          setSelectedIdentity(null);
        }}
        footer={null}
        centered
        width={800}
        styles={{
          body: {
            maxHeight: 'calc(100vh - 200px)',
            overflowY: 'auto',
          },
        }}
      >
        {selectedIdentity && (
          <div>
            <IdentityCard identity={selectedIdentity} />

            {/* 身份职业 */}
            <div style={{ marginTop: 16 }}>
              <IdentityCareerCard
                identityId={selectedIdentity.id}
                onRefresh={onRefresh}
              />
            </div>

            {/* 认知关系 */}
            <div style={{ marginTop: 16 }}>
              <IdentityKnowledgeList
                identityId={selectedIdentity.id}
                characterId={characterId}
                onRefresh={onRefresh}
              />
            </div>
          </div>
        )}
      </Modal>
    </>
  );
};

export default IdentityList;
