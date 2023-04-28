import React, {
  useContext,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import type { InputRef } from "antd";
import Title from "../../components/Title";
import { Button, Form, Input, Popconfirm, message, Table } from "antd";
import type { FormInstance } from "antd/es/form";
import styled from "styled-components";
const NsgaViewBox = styled.div`
  padding: 1rem;
  display: flex;
  flex-direction: column;
`;
const EditableContext = React.createContext<FormInstance<any> | null>(null);

interface Item {
  key: string;
  name: string;
  age: string;
  address: string;
}

interface EditableRowProps {
  index: number;
}

const EditableRow: React.FC<EditableRowProps> = ({ index, ...props }) => {
  const [form] = Form.useForm();
  return (
    <Form form={form} component={false}>
      <EditableContext.Provider value={form}>
        <tr {...props} />
      </EditableContext.Provider>
    </Form>
  );
};

interface EditableCellProps {
  title: React.ReactNode;
  editable: boolean;
  children: React.ReactNode;
  dataIndex: keyof Item;
  record: Item;
  handleSave: (record: Item) => void;
}

const EditableCell: React.FC<EditableCellProps> = ({
  title,
  editable,
  children,
  dataIndex,
  record,
  handleSave,
  ...restProps
}) => {
  const [editing, setEditing] = useState(false);
  const inputRef = useRef<InputRef>(null);
  const form = useContext(EditableContext)!;

  useEffect(() => {
    if (editing) {
      inputRef.current!.focus();
    }
  }, [editing]);

  const toggleEdit = () => {
    setEditing(!editing);
    form.setFieldsValue({ [dataIndex]: record[dataIndex] });
  };

  const save = async () => {
    try {
      const values = await form.validateFields();

      toggleEdit();
      handleSave({ ...record, ...values });
    } catch (errInfo) {
      console.log("Save failed:", errInfo);
    }
  };

  let childNode = children;

  if (editable) {
    childNode = editing ? (
      <Form.Item
        style={{ margin: 0 }}
        name={dataIndex}
        rules={[
          {
            required: true,
            message: `${title} is required.`,
          },
        ]}
      >
        <Input ref={inputRef} onPressEnter={save} onBlur={save} />
      </Form.Item>
    ) : (
      <div
        className="editable-cell-value-wrap"
        style={{ paddingRight: 24 }}
        onClick={toggleEdit}
      >
        {children}
      </div>
    );
  }

  return <td {...restProps}>{childNode}</td>;
};

type EditableTableProps = Parameters<typeof Table>[0];

interface DataType {
  key: React.Key;
  para: string;
  explaination: string;
  unit: string;
  lower: number;
  upper: number;
  default: number;
  value?: number;
}

type ColumnTypes = Exclude<EditableTableProps["columns"], undefined>;

const NsgaView: React.FC = () => {
  const [dataSource, setDataSource] = useState<DataType[]>([]);
  const [messageApi, contextHolder] = message.useMessage();

  const defaultColumns: (ColumnTypes[number] & {
    editable?: boolean;
    dataIndex: string;
  })[] = [
    {
      title: "参数",
      dataIndex: "para",
      width: "12%",
    },
    {
      title: "参数含义",
      dataIndex: "explaination",
      width: "30%",
    },
    {
      title: "参数单位",
      dataIndex: "unit",
      width: "6%",
    },
    {
      title: "参数下限",
      dataIndex: "lower",
    },
    {
      title: "参数上限",
      dataIndex: "upper",
    },
    {
      title: "默认值",
      dataIndex: "default",
    },
    {
      title: "参数值",
      dataIndex: "value",
      editable: true,
    },
  ];

  const handleSave = (row: DataType) => {
    let { value: inputValue, upper, lower } = row;
    inputValue = Number(inputValue);
    if (inputValue < lower || inputValue > upper) {
      message.error("参数超出范围，请重新设置！");
    } else {
      const newData = [...dataSource];
      const index = newData.findIndex((item) => row.para === item.para);
      const item = newData[index];
      newData.splice(index, 1, {
        ...item,
        ...row,
      });
      setDataSource(newData);
      message.success("设置成功！");
    }
  };

  const components = {
    body: {
      row: EditableRow,
      cell: EditableCell,
    },
  };

  const columns = defaultColumns.map((col) => {
    if (!col.editable) {
      return col;
    }
    return {
      ...col,
      onCell: (record: DataType) => ({
        record,
        editable: col.editable,
        dataIndex: col.dataIndex,
        title: col.title,
        handleSave,
      }),
    };
  });
  const submitParams = async (): void => {
    await window.electronAPI.updateParas(dataSource);
    message.success("参数保存成功！");
  };
  useLayoutEffect(() => {
    let fetchData = async () => {
      let res = await window.electronAPI.requireParas();
      setDataSource(res);
    };
    fetchData();
  }, []);

  return (
    <NsgaViewBox>
      <Title title="模型参数" />
      <Table
        components={components}
        rowClassName={() => "editable-row"}
        bordered
        dataSource={dataSource}
        columns={columns as ColumnTypes}
      />
      <Button
        type="primary"
        style={{ width: 201 }}
        size="large"
        onClick={submitParams}
      >
        提交修改
      </Button>
      {contextHolder}
    </NsgaViewBox>
  );
};

export default NsgaView;
