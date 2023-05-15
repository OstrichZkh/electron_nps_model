import React, { useEffect, useState, Fragment } from "react";
import styled from "styled-components";
import Title from "../../components/Title";
import { useSelector, useDispatch } from "react-redux";
import { Checkbox, Button, Upload, message, Modal, Select } from "antd";
import type { CheckboxChangeEvent } from "antd/es/checkbox";
import { updateStatusAsync } from "../../store/features/dataManagementSlice.ts";
import * as echarts from "echarts";
import { flushSync } from "react-dom";

type IProps = {};
type KProps = {
  type: "sed" | "col" | "sedP" | "colP" | "solP" | "TP";
  checked: boolean;
  imported: boolean;
};
const ModelRunBox = styled.div`
  padding: 1rem;
  display: flex;
  flex-direction: column;
`;
const ModelRunView = (props: IProps) => {
  let { curProjectInfo } = useSelector((state) => state.dataManagementReducer);
  let [calibrateInfo, setCalibreateInfo]: [any, Function] = useState(null);
  let [calibrateOptions, setCalibrateOptions]: [any, Function] = useState([]);
  let [curInfo, setCurinfo]: [any, Function] = useState({});
  let [echartsOptions, setEchartsOptions] = useState({});
  // 检查率定数据情况
  useEffect(() => {
    // 首次进入，立马查询率定数据
    setTimeout(() => {
      (async () => {
        let { status, msg: calibrateInfos } =
          await window.electronAPI.requireCalibrateInfo();
        let calibrateArr: any[] = [];
        let cabOptions: any[] = [];

        for (let key in calibrateInfos) {
          calibrateArr.push({
            ...calibrateInfos[key],
            timeStamp: +key,
          });
        }
        calibrateArr.sort((a, b) => {
          return b.timeStamp - a.timeStamp;
        });
        calibrateArr.map((item, index) => {
          cabOptions.push({
            value: item["timeStamp"],
            label: `第${calibrateArr.length - index}次`,
          });
        });
        setCalibreateInfo(calibrateArr);
        setCalibrateOptions(cabOptions);
      })();
    }, 0);

    // 每10秒请求最新的率定信息
    let timer = setInterval(() => {}, 10 * 1000);
    return () => {
      clearInterval(timer);
    };
  }, []);
  useEffect(() => {
    let newOptions: any = { ...echartsOptions };
    Object.keys(curInfo).map((key, index) => {
      if (key !== "timeStamp") {
        let myChart = echarts.init(
          document.querySelector(`.echarts-${key}`) as HTMLElement
        );
        window.onresize = function () {
          myChart.resize();
        };
        let { r2, nse, re_, obs, pre } = curInfo[key];
        let xaxis: number[] = [];
        pre.forEach((itm, idx) => {
          xaxis.push(idx);
        });
        let echartsOption = {
          legend: {
            data: ["观测值", "模拟值"],
          },
          xAxis: {
            type: "category",
            data: xaxis,
          },
          yAxis: {
            type: "value",
          },
          title: {
            text: key,
          },
          series: [
            {
              name: "观测值",
              type: "line",
              data: obs,
            },
            {
              name: "模拟值",
              type: "line",
              data: pre,
            },
          ],
        };

        newOptions[key] = echartsOption;
      }
      setEchartsOptions(newOptions);
    });
  }, [curInfo]);
  useEffect(() => {
    console.log(curInfo, echartsOptions, 123);
    Object.keys(echartsOptions).map((key, index) => {
      if (key !== "timeStamp") {
        console.log(`.echarts-${key}`);
        let myChart = echarts.init(
          document.querySelector(`.echarts-${key}`) as HTMLElement
        );
        myChart.clear();
        myChart.setOption(echartsOptions[key]);
      }
    });
  }, [JSON.stringify(echartsOptions)]);
  const handleOpsChange = (e) => {
    let curInfo_ = calibrateInfo.filter((item) => item.timeStamp == e)[0];
    setCurinfo(curInfo_);
  };
  return (
    <ModelRunBox>
      <Title title="请选择率定目标" />
      {Object.keys(curProjectInfo["observeData"]).map((key) => {
        return (
          <CalibrateSelector
            key={key}
            type={key}
            {...curProjectInfo["observeData"][key]}
          />
        );
      })}
      <div style={{ display: "flex" }} className="button-selector-wrapper">
        <Button type="primary" style={{ width: 120, marginRight: "1rem" }}>
          运行模型
        </Button>
        <Select
          // defaultValue="lucy"
          style={{ width: 120 }}
          onChange={handleOpsChange}
          options={calibrateOptions}
        />
      </div>
      <div className="charts-box">
        {Object.keys(curInfo).map((key, index) => {
          if (key !== "timeStamp") {
            return (
              <Fragment key={key}>
                <div
                  style={{
                    width: "100rem",
                    height: "20rem",
                    margin: "2rem 0",
                  }}
                  className={`echarts-${key}`}
                ></div>
              </Fragment>
            );
          }
        })}
      </div>
    </ModelRunBox>
  );
};

const CalibrateSelectorBox = styled.div`
  display: flex;
  height: 3rem;
  .check-box {
    align-self: center;
  }
  .check-box-text {
    font-size: 1rem;
  }
  .data-importer {
    align-self: center;
  }
`;
const titleReflect = {
  sed: "泥沙",
  col: "胶体",
  sedP: "大颗粒态磷",
  colP: "胶体磷",
  solP: "溶解态磷",
  TP: "总磷",
};
const CalibrateSelector = (props: KProps) => {
  const [messageApi, contextHolder] = message.useMessage();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const dispatch = useDispatch();
  const onChange = (e: CheckboxChangeEvent) => {
    dispatch(
      updateStatusAsync([
        {
          target: ["observeData", props.type, "checked"],
          value: e.target.checked,
        },
      ])
    );
  };

  const importData = async (e) => {
    const { originFileObj: targetFile } = e.fileList[0];
    let extension = targetFile.name.split(".")[1];
    if (extension !== "txt") {
      message.error("请上传txt文件！");
      return;
    }
    let respose = await window.electronAPI.uploadFile({
      filePath: targetFile.path,
      type: props.type,
    });
    if (respose.status == 200) {
      message.success("上传成功！");
      dispatch(
        updateStatusAsync([
          {
            target: ["observeData", props.type, "imported"],
            value: true,
          },
        ])
      );
      return;
    } else {
      message.success("上传失败！");
      return;
    }
  };
  const showModal = () => {
    setIsModalOpen(true);
  };
  const deleteData = async () => {
    setIsModalOpen(false);
    let response = await window.electronAPI.deleteFile({
      type: props.type,
    });
    if (response.status == 200) {
      message.success("删除成功！");
      dispatch(
        updateStatusAsync([
          {
            target: ["observeData", props.type, "imported"],
            value: false,
          },
        ])
      );
    }
  };

  return (
    <CalibrateSelectorBox>
      <div className="check-box">
        <Checkbox defaultChecked={props.checked} onChange={onChange}>
          <div className="check-box-text">{titleReflect[props.type]}</div>
        </Checkbox>
      </div>
      <div className="data-importer">
        {props.checked &&
          (props.imported ? (
            <Fragment>
              <Button onClick={showModal} danger size="middle">
                删除观测数据
              </Button>
              <Modal
                title="是否确认删除？"
                open={isModalOpen}
                onOk={deleteData}
                onCancel={() => {
                  setIsModalOpen(false);
                }}
              ></Modal>
            </Fragment>
          ) : (
            <Upload
              beforeUpload={() => false}
              fileList={[]}
              showUploadList={false}
              onChange={importData}
            >
              <Button type="primary" size="middle">
                导入观测数据
              </Button>
            </Upload>
          ))}
      </div>
      {contextHolder}
    </CalibrateSelectorBox>
  );
};

export default ModelRunView;
