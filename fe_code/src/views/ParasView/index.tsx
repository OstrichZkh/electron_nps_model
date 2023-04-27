import React, { useState } from "react";
import Title from "../../components/Title";
import styled from "styled-components";
import { Button, message, Form, Input } from "antd";
import { useSelector, useDispatch } from "react-redux";
import { updateStatusAsync } from "../../store/features/dataManagementSlice.ts";

type IProps = {};
const NsgaViewBox = styled.div`
  padding: 1rem;
  display: flex;
  flex-direction: column;
`;
const ParaView = (props: IProps) => {
  let { curProjectInfo } = useSelector(
    (state: any) => state.dataManagementReducer
  );
  const [messageApi, contextHolder] = message.useMessage();

  let [nsgaParams, setNsgaParams] = useState(
    curProjectInfo.nsga ? curProjectInfo.nsga : {}
  );
  let dispatch = useDispatch();
  const handleChange = (e: any, key: string): void => {
    const { value: inputValue } = e.target;
    setNsgaParams({
      ...nsgaParams,
      [key]: inputValue,
    });
  };
  const submitNsga = () => {
    if (+nsgaParams.population != nsgaParams.population) {
      message.error("种群数量请输入数字！");
      return;
    }
    if (+nsgaParams.iteration != nsgaParams.iteration) {
      message.error("迭代次数请输入数字！");
      return;
    }
    if (+nsgaParams.mutation != nsgaParams.mutation) {
      message.error("变异概率请输入数字！");
      return;
    }
    if (+nsgaParams.mutation <= 0 || +nsgaParams.mutation >= 1) {
      message.error("变异概率请输入介于0~1之间的数字！");
      return;
    }

    let payload = [
      {
        target: ["nsga"],
        value: nsgaParams,
      },
    ];
    dispatch(updateStatusAsync(payload));
  };
  return (
    <NsgaViewBox>
      <Title title="模型率定参数设置" />
      <Form
        size="large"
        name="basic"
        wrapperCol={{ span: 16 }}
        style={{ maxWidth: 300 }}
        autoComplete="off"
      >
        <Form.Item
          label="种群数量"
          name="population"
          rules={[{ required: true, message: "请输入种群数量！" }]}
        >
          <Input
            onChange={(e) => {
              handleChange(e, "population");
            }}
            defaultValue={nsgaParams.population}
          />
        </Form.Item>
        <Form.Item
          label="迭代次数"
          name="iteration"
          rules={[{ required: true, message: "请输入迭代次数！" }]}
        >
          <Input
            onChange={(e) => {
              handleChange(e, "iteration");
            }}
            defaultValue={nsgaParams.iteration}
          />
        </Form.Item>

        <Form.Item
          label="变异概率"
          name="mutation"
          rules={[{ required: true, message: "请输入变异概率" }]}
        >
          <Input
            onChange={(e) => {
              handleChange(e, "mutation");
            }}
            defaultValue={nsgaParams.mutation}
          />
        </Form.Item>

        <Form.Item wrapperCol={{ offset: 8, span: 16 }}>
          <Button onClick={submitNsga} type="primary">
            提交
          </Button>
        </Form.Item>
      </Form>
      {contextHolder}
    </NsgaViewBox>
  );
};

export default ParaView;
