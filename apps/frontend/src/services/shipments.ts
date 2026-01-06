import { apiClient } from './api';

export interface Shipment {
  shipment: {
    id: string;
    supplier: string;
    warehouse: string;
    route_type: string;
    current_status: string | null;
    bags: Array<{
      bag_id: string;
      sizes: Record<string, number>;
    }>;
    totals: {
      bags: number;
      pieces: number;
    };
  };
  events: Array<{
    id: number;
    status: string;
    changed_by: number;
    changed_at: string;
  }>;
}

export interface StatusUpdateRequest {
  action: 'SENT_FROM_FACTORY' | 'SHIPPED_FROM_FF' | 'DELIVERED';
}

export interface ShipmentListItem {
  id: string;
  supplier: string;
  warehouse: string;
  current_status: string | null;
  total_bags: number;
  total_pieces: number;
  created_at: string;
  updated_at: string;
}

export interface ListShipmentsParams {
  status?: string;
  limit?: number;
  offset?: number;
}

export const shipmentService = {
  async listShipments(params?: ListShipmentsParams): Promise<ShipmentListItem[]> {
    const queryParams = new URLSearchParams();

    if (params?.status) {
      queryParams.append('status', params.status);
    }
    if (params?.limit !== undefined) {
      queryParams.append('limit', params.limit.toString());
    }
    if (params?.offset !== undefined) {
      queryParams.append('offset', params.offset.toString());
    }

    const query = queryParams.toString();
    const url = query ? `/api/shipments?${query}` : '/api/shipments';

    return apiClient.get<ShipmentListItem[]>(url);
  },

  async getShipment(shipmentId: string): Promise<Shipment> {
    return apiClient.get<Shipment>(`/api/shipments/${shipmentId}`);
  },

  async updateStatus(
    shipmentId: string,
    status: StatusUpdateRequest,
    idempotencyKey?: string
  ): Promise<any> {
    return apiClient.post(`/api/shipments/${shipmentId}/events`, status);
  }
};
