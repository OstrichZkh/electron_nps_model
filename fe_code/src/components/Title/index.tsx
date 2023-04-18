import React from "react";
import styled from "styled-components";

const TitleBox = styled.div`
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  font-size: 2rem;
  font-weight: bold;
  font-family: "Times New Roman", Times, serif;
  border-bottom: 2px solid rgb(200, 200, 200);
  width: 80vw;
`;

const Title = (props: any) => {
  return <TitleBox>{props.title}</TitleBox>;
};

export default Title;
