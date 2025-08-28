import { useState, useEffect } from "react";
import { Form, Button, Row, Col } from "react-bootstrap";

interface DeviceFormData {
  name: string;
  device_type: string;
  ip_address: string;
  port: number;
  username: string;
  password?: string; // Optional for editing
  secret?: string; // Optional for editing
}

interface DeviceFormProps {
  initialData?: DeviceFormData;
  onSubmit: (data: DeviceFormData) => void;
  isEditMode?: boolean;
}

const DeviceForm = ({ initialData, onSubmit, isEditMode = false }: DeviceFormProps) => {
  const [name, setName] = useState(initialData?.name || "");
  const [deviceType, setDeviceType] = useState(initialData?.device_type || "");
  const [ipAddress, setIpAddress] = useState(initialData?.ip_address || "");
  const [port, setPort] = useState<number>(initialData?.port || 22);
  const [username, setUsername] = useState(initialData?.username || "");
  const [password, setPassword] = useState(""); // Always empty for security
  const [secret, setSecret] = useState(""); // Always empty for security

  useEffect(() => {
    if (initialData) {
      setName(initialData.name);
      setDeviceType(initialData.device_type);
      setIpAddress(initialData.ip_address);
      setPort(initialData.port);
      setUsername(initialData.username);
      // Passwords and secrets are not pre-filled for security reasons
    }
  }, [initialData]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      name,
      device_type: deviceType,
      ip_address: ipAddress,
      port,
      username,
      ...(password && { password }), // Only include if not empty
      ...(secret && { secret }),     // Only include if not empty
    });
  };

  return (
    <Form onSubmit={handleSubmit}>
      <Form.Group className="mb-3" controlId="deviceName">
        <Form.Label>Device Name</Form.Label>
        <Form.Control
          type="text"
          placeholder="Enter device name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
      </Form.Group>

      <Form.Group className="mb-3" controlId="deviceType">
        <Form.Label>Device Type</Form.Label>
        <Form.Select
          value={deviceType}
          onChange={(e) => setDeviceType(e.target.value)}
          required
        >
          <option value="">Select a device type</option>
          <option value="cisco_ios_router">Cisco IOS Router</option>
          <option value="cisco_ios_switch">Cisco IOS Switch</option>
          <option value="aruba_procurve">Aruba Procurve</option>
          <option value="ubiquiti_edgerouter">Ubiquiti Edge Router</option>
          <option value="ubiquiti_edgeswitch">Ubiquiti Unifi Switch</option>
          <option value="juniper_junos">Juniper Junos</option> {/* Added Aruba option */}
        </Form.Select>
      </Form.Group>

      <Form.Group className="mb-3" controlId="ipAddress">
        <Form.Label>IP Address</Form.Label>
        <Form.Control
          type="text"
          placeholder="e.g., 192.168.1.1"
          value={ipAddress}
          onChange={(e) => setIpAddress(e.target.value)}
          required
        />
      </Form.Group>

      <Form.Group className="mb-3" controlId="port">
        <Form.Label>Port</Form.Label>
        <Form.Control
          type="number"
          placeholder="e.g., 22"
          value={port}
          onChange={(e) => setPort(Number(e.target.value))}
          required
        />
      </Form.Group>

      <Form.Group className="mb-3" controlId="username">
        <Form.Label>Username</Form.Label>
        <Form.Control
          type="text"
          placeholder="Enter username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
      </Form.Group>

      <Form.Group className="mb-3" controlId="password">
        <Form.Label>Password {isEditMode && "(Leave blank to keep current)"}</Form.Label>
        <Form.Control
          type="password"
          placeholder={isEditMode ? "Leave blank to keep current password" : "Enter password"}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required={!isEditMode} // Required only for add mode
        />
      </Form.Group>

      <Form.Group className="mb-3" controlId="secret">
        <Form.Label>Secret {isEditMode && "(Leave blank to keep current)"}</Form.Label>
        <Form.Control
          type="password"
          placeholder={isEditMode ? "Leave blank to keep current secret (optional)" : "Enter secret (optional)"}
          value={secret}
          onChange={(e) => setSecret(e.target.value)}
        />
      </Form.Group>

      <Button variant="primary" type="submit">
        {isEditMode ? "Update Device" : "Add Device"}
      </Button>
    </Form>
  );
};

export default DeviceForm;
