
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./useAuth";

// Define the types for device data
interface Device {
  id: string;
  name: string;
  device_type: string;
  ip_address: string;
  port: number;
  username: string;
}

interface DeviceDetail extends Device {
  version: string;
  interfaces: {
    interface: string;
    ip_address: string;
    status: string;
    proto: string;
  }[];
  hostname?: string;
  activeUsers?: any[];
  localUsers?: any[];
  clock?: string;
  vlanDetails?: any[];
  vtpStatus?: any[];
  spanningTreeSummary?: any[];
  interfacesTrunk?: any[];
  lineConfig?: string[];
  banners?: { [key: string]: string };
  ntpConfig?: any[];
  snmpConfig?: any[];
  loggingConfig?: any[];
  acls?: any[];
  aaaConfig?: any[];
  cdpNeighbors?: any[];
  ospfNeighbors?: any[];
  eigrpNeighbors?: any[];
  routingProtocolConfig?: any[];
  natConfig?: any[];
  vpnConfig?: any[];
  lldpNeighbors?: any[];
  portSecurity?: any[];
  etherchannelSummary?: any[];
  vlanConfig?: any[];
  interfaceVlanMembership?: any[];
}

// State for the hook
interface DeviceDetailsState {
  device: DeviceDetail | null;
  loading: boolean;
  errors: { [key: string]: string | null };
}

// The custom hook
export const useDeviceDetails = (deviceId: string | undefined) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();
  const [state, setState] = useState<DeviceDetailsState>({
    device: null,
    loading: true,
    errors: {},
  });

  useEffect(() => {
    if (!deviceId) {
      setState({
        device: null,
        loading: false,
        errors: { general: "No device ID provided." },
      });
      return;
    }

    const fetchAllDetails = async () => {
      if (!token) {
        logout();
        navigate("/login");
        return;
      }

      setState({
        device: null,
        loading: true,
        errors: {},
      });

      const headers = {
        Authorization: `Bearer ${token}`,
      };

      // Helper to fetch individual details and handle errors
      const fetchDetail = async (url: string, key: string) => {
        try {
          const response = await fetch(url, { headers });
          if (response.status === 401) {
            logout();
            navigate("/login");
            return null;
          }
          if (!response.ok) {
            throw new Error(`Failed to fetch ${key}`);
          }
          return await response.json();
        } catch (error: any) {
          setState((prevState) => ({
            ...prevState,
            errors: {
              ...prevState.errors,
              [key]: error.message || `Failed to fetch ${key}`,
            },
          }));
          return null;
        }
      };

      // Fetch primary device details first
      const primaryDetails = await fetchDetail(
        `/api/devices/${deviceId}`,
        "primary"
      );

      if (!primaryDetails) {
        setState((prevState) => ({
          ...prevState,
          loading: false,
          errors: {
            ...prevState.errors,
            primary: "Failed to fetch essential device details.",
          },
        }));
        return;
      }

      // Fetch all other details in parallel
      const detailEndpoints: { key: keyof DeviceDetail; url: string }[] = [
        { key: "hostname", url: `/api/devices/${deviceId}/hostname` },
        { key: "activeUsers", url: `/api/devices/${deviceId}/active-users` },
        { key: "localUsers", url: `/api/devices/${deviceId}/local-users` },
        { key: "clock", url: `/api/devices/${deviceId}/clock` },
        { key: "vlanDetails", url: `/api/devices/${deviceId}/vlan-details` },
        { key: "vtpStatus", url: `/api/devices/${deviceId}/vtp-status` },
        { key: "spanningTreeSummary", url: `/api/devices/${deviceId}/spanning-tree-summary` },
        { key: "interfacesTrunk", url: `/api/devices/${deviceId}/interfaces-trunk` },
        { key: "lineConfig", url: `/api/devices/${deviceId}/line-config` },
        { key: "banners", url: `/api/devices/${deviceId}/banners` },
        { key: "ntpConfig", url: `/api/devices/${deviceId}/ntp-config` },
        { key: "snmpConfig", url: `/api/devices/${deviceId}/snmp-config` },
        { key: "loggingConfig", url: `/api/devices/${deviceId}/logging-config` },
        { key: "acls", url: `/api/devices/${deviceId}/acls` },
        { key: "aaaConfig", url: `/api/devices/${deviceId}/aaa-config` },
        { key: "cdpNeighbors", url: `/api/devices/${deviceId}/cdp-neighbors` },
        { key: "ospfNeighbors", url: `/api/devices/${deviceId}/ospf-neighbors` },
        { key: "eigrpNeighbors", url: `/api/devices/${deviceId}/eigrp-neighbors` },
        { key: "routingProtocolConfig", url: `/api/devices/${deviceId}/routing-protocol-config` },
        { key: "natConfig", url: `/api/devices/${deviceId}/nat-config` },
        { key: "vpnConfig", url: `/api/devices/${deviceId}/vpn-config` },
        { key: "lldpNeighbors", url: `/api/devices/${deviceId}/lldp-neighbors` },
        { key: "portSecurity", url: `/api/devices/${deviceId}/port-security` },
        { key: "etherchannelSummary", url: `/api/devices/${deviceId}/etherchannel-summary` },
        { key: "vlanConfig", url: `/api/devices/${deviceId}/vlan-config` },
        { key: "interfaceVlanMembership", url: `/api/devices/${deviceId}/interface-vlan-membership` },
      ];

      const results = await Promise.all(
        detailEndpoints.map((ep) => fetchDetail(ep.url, ep.key))
      );

      const additionalDetails = detailEndpoints.reduce((acc, ep, index) => {
        if (results[index] !== null) {
          acc[ep.key] = results[index];
        }
        return acc;
      }, {} as Partial<DeviceDetail>);

      setState((prevState) => ({
        ...prevState,
        device: { ...primaryDetails, ...additionalDetails },
        loading: false,
      }));
    };

    fetchAllDetails();
  }, [deviceId, token, navigate, logout]);

  return state;
};
