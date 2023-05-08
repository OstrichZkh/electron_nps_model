import React, { useEffect, useState, useRef } from "react";
import Title from "../../components/Title";
import styled from "styled-components";
import { Button, Table, Space, Tag, Modal, Form, Input, Select } from "antd";
import { useSelector, useDispatch } from "react-redux";
import type { ColumnsType } from "antd/es/table";
import { updateStatusAsync } from "../../store/features/dataManagementSlice.ts";
const { Column, ColumnGroup } = Table;

interface DataType {
  key: React.Key;
  name: string;
  landuse: string;
  amount: number;
  N_ration: number;
  P_ration: number;
  applyMonth: number;
  description: string;
  actions: any;
}

type IProps = {};
const FertViewBox = styled.div`
  padding: 1rem;
  display: flex;
  flex-direction: column;
`;

const landuseOptions = [
  { value: "forest", label: "林地" },
  { value: "paddy", label: "水田" },
  { value: "water", label: "水体" },
  { value: "sloping", label: "坡耕地" },
  { value: "construct", label: "建设用地" },
];
const FertView = (props: IProps) => {
  let { curProjectInfo } = useSelector(
    (state: any) => state.dataManagementReducer
  );
  const dispatch = useDispatch();
  /* Talbes相关 */
  let [measures, setMeasures]: [any, Function] = useState(
    curProjectInfo.measures ? curProjectInfo.measures : []
  );
  const [form] = Form.useForm();
  const columns = [
    {
      title: "措施名称",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "土地利用类型",
      dataIndex: "landuse",
      key: "landuse",
    },
    {
      title: "施用量(kg)",
      dataIndex: "amount",
      key: "amount",
    },
    {
      title: "氮比例",
      dataIndex: "N_ration",
      key: "N_ration",
    },
    {
      title: "磷比例",
      dataIndex: "P_ration",
      key: "P_ration",
    },
    {
      title: "施用月份",
      dataIndex: "applyMonth",
      key: "applyMonth",
    },
    {
      title: "描述",
      dataIndex: "description",
      key: "description",
    },
    {
      title: "操作",
      dataIndex: "actions",
      key: "actions",
      render: (_, record) => {
        return (
          <Space size="middle">
            <a
              onClick={() => {
                deleteMeasures(record);
              }}
            >
              删除措施
            </a>
          </Space>
        );
      },
    },
  ];
  const addMeasures = (): void => {};
  const deleteMeasures = (target): void => {
    let newMeasures = measures.filter((item) => {
      return item.name !== target.name;
    });
    setMeasures(newMeasures);
    let payload = [
      {
        target: ["measures"],
        value: newMeasures,
      },
    ];
    dispatch(updateStatusAsync(payload));
  };
  // 添加措施相关
  const [isModalOpen, setIsModalOpen] = useState(false);
  /* 正在编辑的弹窗中的信息 */
  const [infoEdited, setInfoEdited]: [any, Function] = useState({});
  const showModal = () => {
    setIsModalOpen(true);
  };
  const handleOk = () => {
    let validate =
      infoEdited.name &&
      infoEdited.landuse &&
      infoEdited.amount &&
      +infoEdited.amount == Number(infoEdited.amount) &&
      infoEdited.N_ration >= 0 &&
      infoEdited.N_ration <= 1 &&
      infoEdited.P_ration >= 0 &&
      infoEdited.P_ration <= 1
        ? true
        : false;
    form.submit();

    if (validate) {
      setMeasures((pre) => [infoEdited, ...pre]);
      let payload = [
        {
          target: ["measures"],
          value: [infoEdited, ...measures],
        },
      ];
      dispatch(updateStatusAsync(payload));
      setIsModalOpen(false);
      setInfoEdited({});
      form.resetFields();
    }
  };
  const handleCancel = () => {
    setInfoEdited({});
    form.resetFields();

    setIsModalOpen(false);
  };

  const handleNameChange = (e) => {
    const { value: inputValue } = e.target;
    setInfoEdited({
      ...infoEdited,
      name: inputValue,
    });
  };
  const handleLuChange = (e) => {
    setInfoEdited({
      ...infoEdited,
      landuse: e,
    });
  };
  const handleAmountChange = (e) => {
    const { value: inputValue } = e.target;
    setInfoEdited({
      ...infoEdited,
      amount: inputValue,
    });
  };
  const handleNitroChange = (e) => {
    const { value: inputValue } = e.target;
    setInfoEdited({
      ...infoEdited,
      N_ration: inputValue,
    });
  };
  const handlePhoChange = (e) => {
    const { value: inputValue } = e.target;
    setInfoEdited({
      ...infoEdited,
      P_ration: inputValue,
    });
  };
  const handleMonthChange = (e) => {
    const { value: inputValue } = e.target;
    setInfoEdited({
      ...infoEdited,
      applyMonth: inputValue,
    });
  };

  return (
    <FertViewBox>
      <Title title="农业措施设置" />
      <Table dataSource={measures}>
        {columns.map((item) => {
          return <Column {...item} />;
        })}
      </Table>
      <Button
        style={{ width: 120, marginTop: "1rem" }}
        type="primary"
        size="large"
        onClick={showModal}
      >
        添加措施
      </Button>
      <Modal
        title="新建措施"
        open={isModalOpen}
        onOk={handleOk}
        onCancel={handleCancel}
        width={800}
      >
        <Form
          name="basic"
          style={{ width: 400, margin: "2rem auto" }}
          form={form}
          // onFinish={onFinish}
          // onFinishFailed={onFinishFailed}
          autoComplete="off"
        >
          <Form.Item
            label="措施名称"
            name="name"
            rules={[{ required: true, message: "请输入名称" }]}
          >
            <Input
              onChange={(e) => {
                handleNameChange(e);
              }}
              placeholder="请输入名称(务必确保唯一)"
            />
          </Form.Item>
          <Form.Item
            label="土地利用类型"
            name="landuse"
            rules={[{ required: true, message: "请选择土地利用类型" }]}
          >
            <Select
              onChange={(e) => {
                handleLuChange(e);
              }}
              options={landuseOptions}
            />
          </Form.Item>
          <Form.Item
            label="化肥施用量(kg)"
            name="amount"
            rules={[{ required: true, message: "请输入化肥施用量" }]}
          >
            <Input
              onChange={(e) => {
                handleAmountChange(e);
              }}
              value={infoEdited.amount}
              placeholder="请输入纯数字"
            />
          </Form.Item>
          <Form.Item
            label="氮占比(0~1)"
            name="N_ration"
            rules={[{ required: true, message: "请输入氮占比" }]}
          >
            <Input
              onChange={(e) => {
                handleNitroChange(e);
              }}
              placeholder="请输入0~1之间的浮点数"
            />
          </Form.Item>
          <Form.Item
            label="磷占比(0~1)"
            name="P_ration"
            rules={[{ required: true, message: "请输入磷占比" }]}
          >
            <Input
              onChange={(e) => {
                handlePhoChange(e);
              }}
              placeholder="请输入0~1之间的浮点数"
            />
          </Form.Item>
          <Form.Item
            label="化肥施用月份"
            name="applyMonth"
            rules={[{ required: true, message: "请输入化肥施用月份" }]}
          >
            <Input
              onChange={(e) => {
                handleMonthChange(e);
              }}
              placeholder="请输入1~12之间的整数"
            />
          </Form.Item>
        </Form>
      </Modal>
    </FertViewBox>
  );
};

export default FertView;
